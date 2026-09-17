<?php

namespace App\Controller\Api;

use App\Repository\MeetingRepository;
use App\Service\OutputFileManager;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\BinaryFileResponse;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\ResponseHeaderBag;
use Symfony\Component\Routing\Attribute\Route;

/**
 * Zastępuje ręczne odsłuchiwanie próbek audio + edycję <nazwa>.speakers.json
 * w edytorze tekstu (patrz scripts/extract_speaker_samples.py,
 * scripts/identify_speakers.py). Plik na dysku zostaje źródłem prawdy —
 * dokładnie ten sam, który czyta scripts/clean_transcript.py.
 */
#[Route('/api/meetings/{id}')]
class SpeakerController extends AbstractController
{
    public function __construct(
        private readonly MeetingRepository $meetings,
        private readonly OutputFileManager $files,
    ) {
    }

    #[Route('/speakers', name: 'api_speakers_list', methods: ['GET'])]
    public function list(int $id): JsonResponse
    {
        $meeting = $this->meetings->find($id);
        if (!$meeting) {
            return new JsonResponse(['error' => 'Nie znaleziono spotkania.'], 404);
        }

        $data = $this->files->read($this->speakersPath($meeting->getTranscriptDir(), $meeting->getName()));

        return new JsonResponse(['speakers' => $data['speakers'] ?? []]);
    }

    /**
     * Aktualizuje jednego mówcę — zawsze ustawia source="manual" (to ten
     * sam plik, który współdzielą identify_speakers.py i
     * extract_speaker_samples.py; wpis z UI ma być traktowany jak ręcznie
     * potwierdzony, patrz docs/PROJECT_MEMORY.md).
     */
    #[Route('/speakers/{label}', name: 'api_speakers_update', methods: ['PUT'])]
    public function update(int $id, string $label, Request $request): JsonResponse
    {
        $meeting = $this->meetings->find($id);
        if (!$meeting) {
            return new JsonResponse(['error' => 'Nie znaleziono spotkania.'], 404);
        }

        $payload = json_decode($request->getContent(), true) ?? [];
        $proposedName = isset($payload['proposed_name']) ? trim((string) $payload['proposed_name']) : '';
        $confidence = $payload['confidence'] ?? 'wysoka';

        $path = $this->speakersPath($meeting->getTranscriptDir(), $meeting->getName());
        $data = $this->files->read($path) ?? ['speakers' => []];
        $speakers = $data['speakers'] ?? [];

        $found = false;
        foreach ($speakers as &$speaker) {
            if (($speaker['speaker_label'] ?? null) === $label) {
                $speaker['proposed_name'] = $proposedName !== '' ? $proposedName : null;
                $speaker['confidence'] = $proposedName !== '' ? $confidence : 'brak';
                $speaker['source'] = 'manual';
                $speaker['evidence'] = 'Rozpoznany po głosie (przez interfejs webowy).';
                $found = true;
                break;
            }
        }
        unset($speaker);

        if (!$found) {
            $speakers[] = [
                'speaker_label' => $label,
                'proposed_name' => $proposedName !== '' ? $proposedName : null,
                'confidence' => $proposedName !== '' ? $confidence : 'brak',
                'source' => 'manual',
                'evidence' => 'Rozpoznany po głosie (przez interfejs webowy).',
                'audio_samples' => [],
            ];
        }

        $data['speakers'] = $speakers;
        $this->files->write($path, $data);

        return new JsonResponse(['speakers' => $speakers]);
    }

    #[Route('/speakers/{label}/sample/{n}', name: 'api_speakers_sample', methods: ['GET'], requirements: ['n' => '\d+'])]
    public function sample(int $id, string $label, int $n): BinaryFileResponse
    {
        $meeting = $this->meetings->find($id);
        if (!$meeting) {
            throw $this->createNotFoundException('Nie znaleziono spotkania.');
        }

        $data = $this->files->read($this->speakersPath($meeting->getTranscriptDir(), $meeting->getName()));
        $entry = null;
        foreach ($data['speakers'] ?? [] as $speaker) {
            if (($speaker['speaker_label'] ?? null) === $label) {
                $entry = $speaker;
                break;
            }
        }

        $samples = $entry['audio_samples'] ?? [];
        $relative = $samples[$n - 1] ?? null;
        if (!$relative) {
            throw $this->createNotFoundException('Brak takiej próbki audio.');
        }

        // audio_samples w JSON jest zapisane względem katalogu transkrypcji
        // (patrz scripts/extract_speaker_samples.py), z separatorem '\\' na Windows.
        $relative = str_replace('\\', '/', $relative);
        $fullPath = $this->files->resolvePath('transcripts/' . $meeting->getTranscriptDir() . '/' . $relative);

        if (!is_file($fullPath)) {
            throw $this->createNotFoundException('Plik próbki audio nie istnieje na dysku.');
        }

        $response = new BinaryFileResponse($fullPath);
        $response->headers->set('Content-Type', 'audio/mpeg');
        $response->setContentDisposition(ResponseHeaderBag::DISPOSITION_INLINE);

        return $response;
    }

    #[Route('/transcript', name: 'api_meetings_transcript', methods: ['GET'])]
    public function transcript(int $id): JsonResponse
    {
        $meeting = $this->meetings->find($id);
        if (!$meeting) {
            return new JsonResponse(['error' => 'Nie znaleziono spotkania.'], 404);
        }

        $path = sprintf('transcripts/%s/%s.clean.txt', $meeting->getTranscriptDir(), $meeting->getName());
        $text = $this->files->readText($path);

        if ($text === null) {
            return new JsonResponse([
                'text' => null,
                'error' => 'Brak oczyszczonej transkrypcji — uruchom scripts/clean_transcript.py.',
            ]);
        }

        return new JsonResponse(['text' => $text]);
    }

    private function speakersPath(string $transcriptDir, string $name): string
    {
        return sprintf('transcripts/%s/%s.speakers.json', $transcriptDir, $name);
    }
}
