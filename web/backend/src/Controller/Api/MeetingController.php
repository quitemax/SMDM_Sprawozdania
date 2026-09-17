<?php

namespace App\Controller\Api;

use App\Entity\Meeting;
use App\Entity\MeetingAttendee;
use App\Repository\MemberRepository;
use App\Repository\MeetingRepository;
use App\Service\OutputFileManager;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;

#[Route('/api/meetings')]
class MeetingController extends AbstractController
{
    private const BODIES = ['rada_nadzorcza', 'zarzad', 'inny'];
    private const ROLES = ['protokolant', 'sekretarz', 'przewodniczacy'];

    public function __construct(
        private readonly EntityManagerInterface $em,
        private readonly MeetingRepository $meetings,
        private readonly MemberRepository $members,
        private readonly OutputFileManager $files,
    ) {
    }

    #[Route('', name: 'api_meetings_list', methods: ['GET'])]
    public function list(): JsonResponse
    {
        $meetings = $this->meetings->findBy([], ['transcriptDir' => 'DESC', 'name' => 'ASC']);
        return new JsonResponse(array_map(fn (Meeting $m) => $m->toArray(), $meetings));
    }

    /**
     * Skanuje output/transcripts/**\/*.meeting_info.json i tworzy/aktualizuje
     * wiersze `meetings` — pliki na dysku (tworzone przez
     * scripts/init_meeting_info.py albo przez ten sam endpoint PUT poniżej)
     * są jedynym źródłem prawdy o tym, jakie spotkania istnieją.
     */
    #[Route('/rescan', name: 'api_meetings_rescan', methods: ['POST'])]
    public function rescan(): JsonResponse
    {
        $found = $this->files->scan();
        $seen = [];

        foreach ($found as $entry) {
            $meeting = $this->meetings->findOneByDirAndName($entry['transcript_dir'], $entry['name']);
            if (!$meeting) {
                $meeting = new Meeting();
                $meeting->setTranscriptDir($entry['transcript_dir']);
                $meeting->setName($entry['name']);
                $this->em->persist($meeting);
            }

            $meeting->setMeetingInfoPath($entry['path']);

            $data = $this->files->read($entry['path']) ?? [];
            $meeting->setProtocolNumber($this->emptyToNull($data['protocol_number'] ?? null));
            if (!empty($data['date'])) {
                try {
                    $meeting->setMeetingDate(new \DateTimeImmutable($data['date']));
                } catch (\Exception) {
                    // Data w pliku ma niepoprawny format — zostawiamy null, nie blokujemy skanu.
                }
            }
            $meeting->touch();

            $seen[] = $meeting;
        }

        $this->em->flush();

        return new JsonResponse([
            'scanned' => count($found),
            'meetings' => array_map(fn (Meeting $m) => $m->toArray(), $seen),
        ]);
    }

    #[Route('/{id}/meeting-info', name: 'api_meetings_get_info', methods: ['GET'])]
    public function getMeetingInfo(int $id): JsonResponse
    {
        $meeting = $this->meetings->find($id);
        if (!$meeting) {
            return new JsonResponse(['error' => 'Nie znaleziono spotkania.'], 404);
        }

        $data = $this->files->read($meeting->getMeetingInfoPath()) ?? [];

        return new JsonResponse([
            'meeting' => $meeting->toArray(),
            'meeting_info' => $data,
            // Uczestnicy przypisani w bazie — w UI to one wypełniają formularz
            // (plik na dysku jest tym, co widzą inne skrypty, ale wiersze
            // meeting_attendees odzwierciedlają identycznie tę samą treść).
            'attendees' => array_map(fn (MeetingAttendee $a) => $a->toArray(), $meeting->getAttendees()->toArray()),
        ]);
    }

    /**
     * Zapisuje meeting_info.json NA DYSKU (dokładnie w formacie, którego
     * oczekuje scripts/generate_report.py), a potem synchronizuje
     * meeting_attendees w bazie z tym samym stanem.
     */
    #[Route('/{id}/meeting-info', name: 'api_meetings_put_info', methods: ['PUT'])]
    public function putMeetingInfo(int $id, Request $request): JsonResponse
    {
        $meeting = $this->meetings->find($id);
        if (!$meeting) {
            return new JsonResponse(['error' => 'Nie znaleziono spotkania.'], 404);
        }

        $payload = json_decode($request->getContent(), true) ?? [];

        $attendeeIdsByBody = $payload['attendee_member_ids'] ?? [];
        foreach (self::BODIES as $body) {
            $attendeeIdsByBody[$body] = array_map('intval', $attendeeIdsByBody[$body] ?? []);
        }

        $roleMemberIds = [];
        foreach (self::ROLES as $role) {
            $key = $role . '_member_id';
            $roleMemberIds[$role] = isset($payload[$key]) && $payload[$key] !== null ? (int) $payload[$key] : null;
        }

        // Wczytaj wszystkich potrzebnych Member naraz (unikalne ID z list obecności + ról).
        $allIds = $roleMemberIds;
        foreach ($attendeeIdsByBody as $ids) {
            $allIds = array_merge($allIds, $ids);
        }
        $allIds = array_unique(array_filter($allIds, fn ($v) => $v !== null));
        $membersById = [];
        foreach ($allIds as $memberId) {
            $member = $this->members->find($memberId);
            if ($member) {
                $membersById[$memberId] = $member;
            }
        }

        // Przebuduj meeting_attendees od zera — prościej i bezpieczniej niż
        // próba różnicowego update'u, a liczba osób per spotkanie jest mała.
        $meeting->clearAttendees();
        $this->em->flush();

        $attendeeByMemberId = [];
        foreach (self::BODIES as $body) {
            foreach ($attendeeIdsByBody[$body] as $memberId) {
                if (!isset($membersById[$memberId])) {
                    continue;
                }
                $attendee = new MeetingAttendee();
                $attendee->setMember($membersById[$memberId]);
                $attendee->setBody($body);
                $meeting->addAttendee($attendee);
                $attendeeByMemberId[$memberId] = $attendee;
            }
        }

        foreach (self::ROLES as $role) {
            $memberId = $roleMemberIds[$role];
            if ($memberId === null || !isset($membersById[$memberId])) {
                continue;
            }
            if (isset($attendeeByMemberId[$memberId])) {
                $attendeeByMemberId[$memberId]->setRole($role);
            } else {
                // Protokolant zwykle nie jest formalnym "uczestnikiem" (RN/Zarząd/inni) —
                // dodajemy go jako wpis z body="inny", żeby rola miała gdzie żyć.
                $attendee = new MeetingAttendee();
                $attendee->setMember($membersById[$memberId]);
                $attendee->setBody('inny');
                $attendee->setRole($role);
                $meeting->addAttendee($attendee);
                $attendeeByMemberId[$memberId] = $attendee;
            }
        }

        $protocolNumber = $this->emptyToNull($payload['protocol_number'] ?? null);
        $meeting->setProtocolNumber($protocolNumber);
        $meeting->touch();

        $this->em->flush();

        // Zapis pliku na dysku — dokładnie format scripts/init_meeting_info.py.
        $existing = $this->files->read($meeting->getMeetingInfoPath()) ?? [];
        $fileData = [
            'date' => $existing['date'] ?? $meeting->getMeetingDate()?->format('Y-m-d'),
            'protocol_number' => $protocolNumber,
            'attendees' => [
                'rada_nadzorcza' => $this->namesForBody($meeting, 'rada_nadzorcza'),
                'zarzad' => $this->namesForBody($meeting, 'zarzad'),
                'inni' => $this->namesForInny($meeting),
            ],
            'protokolant' => $this->nameForRole($meeting, 'protokolant'),
            'sekretarz' => $this->nameForRole($meeting, 'sekretarz'),
            'przewodniczacy' => $this->nameForRole($meeting, 'przewodniczacy'),
        ];
        $this->files->write($meeting->getMeetingInfoPath(), $fileData);

        return new JsonResponse([
            'meeting' => $meeting->toArray(),
            'meeting_info' => $fileData,
        ]);
    }

    /** @return list<string> */
    private function namesForBody(Meeting $meeting, string $body): array
    {
        $names = [];
        foreach ($meeting->getAttendees() as $attendee) {
            if ($attendee->getBody() === $body) {
                $names[] = $attendee->getMember()->getFullName();
            }
        }
        return $names;
    }

    /** "inni" dostaje etykietę roli w nawiasie, jeśli Member ją ma (patrz Member::roleLabel). */
    private function namesForInny(Meeting $meeting): array
    {
        $names = [];
        foreach ($meeting->getAttendees() as $attendee) {
            if ($attendee->getBody() !== 'inny') {
                continue;
            }
            $member = $attendee->getMember();
            $label = $member->getRoleLabel();
            $names[] = $label ? sprintf('%s (%s)', $member->getFullName(), $label) : $member->getFullName();
        }
        return $names;
    }

    private function nameForRole(Meeting $meeting, string $role): ?string
    {
        foreach ($meeting->getAttendees() as $attendee) {
            if ($attendee->getRole() === $role) {
                return $attendee->getMember()->getFullName();
            }
        }
        return null;
    }

    private function emptyToNull(?string $value): ?string
    {
        $value = $value !== null ? trim($value) : null;
        return $value === '' ? null : $value;
    }
}
