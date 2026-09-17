<?php

namespace App\Controller\Api;

use App\Entity\Member;
use App\Repository\MemberRepository;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;

#[Route('/api/members')]
class MemberController extends AbstractController
{
    private const VALID_BODIES = ['rada_nadzorcza', 'zarzad', 'inny'];

    public function __construct(
        private readonly EntityManagerInterface $em,
        private readonly MemberRepository $members,
    ) {
    }

    #[Route('', name: 'api_members_list', methods: ['GET'])]
    public function list(Request $request): JsonResponse
    {
        $includeInactive = $request->query->getBoolean('include_inactive');
        $criteria = $includeInactive ? [] : ['active' => true];
        $members = $this->members->findBy($criteria, ['fullName' => 'ASC']);

        return new JsonResponse(array_map(fn (Member $m) => $m->toArray(), $members));
    }

    #[Route('', name: 'api_members_create', methods: ['POST'])]
    public function create(Request $request): JsonResponse
    {
        $data = json_decode($request->getContent(), true) ?? [];

        $error = $this->validate($data);
        if ($error) {
            return new JsonResponse(['error' => $error], 422);
        }

        $member = new Member();
        $member->setFullName(trim($data['full_name']));
        $member->setDefaultBody($data['default_body']);
        $member->setRoleLabel($this->emptyToNull($data['role_label'] ?? null));
        $member->setNotes($this->emptyToNull($data['notes'] ?? null));

        $this->em->persist($member);
        $this->em->flush();

        return new JsonResponse($member->toArray(), 201);
    }

    #[Route('/{id}', name: 'api_members_update', methods: ['PUT'])]
    public function update(int $id, Request $request): JsonResponse
    {
        $member = $this->members->find($id);
        if (!$member) {
            return new JsonResponse(['error' => 'Nie znaleziono osoby.'], 404);
        }

        $data = json_decode($request->getContent(), true) ?? [];

        $error = $this->validate($data);
        if ($error) {
            return new JsonResponse(['error' => $error], 422);
        }

        $member->setFullName(trim($data['full_name']));
        $member->setDefaultBody($data['default_body']);
        $member->setRoleLabel($this->emptyToNull($data['role_label'] ?? null));
        $member->setNotes($this->emptyToNull($data['notes'] ?? null));
        if (array_key_exists('active', $data)) {
            $member->setActive((bool) $data['active']);
        }
        $member->touch();

        $this->em->flush();

        return new JsonResponse($member->toArray());
    }

    #[Route('/{id}', name: 'api_members_delete', methods: ['DELETE'])]
    public function delete(int $id): JsonResponse
    {
        $member = $this->members->find($id);
        if (!$member) {
            return new JsonResponse(['error' => 'Nie znaleziono osoby.'], 404);
        }

        // Miękkie usunięcie — osoba mogła już być przypisana do historycznych
        // spotkań (meeting_attendees), a te wpisy mają zostać nienaruszone.
        $member->setActive(false);
        $member->touch();
        $this->em->flush();

        return new JsonResponse($member->toArray());
    }

    private function validate(array $data): ?string
    {
        if (empty(trim($data['full_name'] ?? ''))) {
            return 'Pole "full_name" jest wymagane.';
        }
        if (!in_array($data['default_body'] ?? null, self::VALID_BODIES, true)) {
            return 'Pole "default_body" musi być jedną z wartości: ' . implode(', ', self::VALID_BODIES) . '.';
        }
        return null;
    }

    private function emptyToNull(?string $value): ?string
    {
        $value = $value !== null ? trim($value) : null;
        return $value === '' ? null : $value;
    }
}
