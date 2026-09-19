<?php

namespace App\Controller\Api;

use App\Service\InputFileManager;
use App\Service\OutputFileManager;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;

/**
 * CRUD nagrań pod input/audio/ — pierwszy krok pipeline'u, zanim
 * scripts/transcribe.py w ogóle wejdzie do gry (uruchamianie samego
 * skryptu to Faza 3 / job runner, patrz docs/ROADMAP.md, Etap 8).
 */
#[Route('/api/recordings')]
class RecordingController extends AbstractController
{
    public function __construct(
        private readonly InputFileManager $input,
        private readonly OutputFileManager $output,
    ) {
    }

    #[Route('', name: 'api_recordings_list', methods: ['GET'])]
    public function list(): JsonResponse
    {
        $recordings = $this->input->scanAudio();

        foreach ($recordings as &$recording) {
            $stem = pathinfo($recording['filename'], PATHINFO_FILENAME);
            $recording['has_transcript'] = $this->output->exists(
                sprintf('transcripts/%s/%s.json', $recording['date_dir'], $stem)
            );
        }
        unset($recording);

        return new JsonResponse($recordings);
    }

    #[Route('', name: 'api_recordings_upload', methods: ['POST'])]
    public function upload(Request $request): JsonResponse
    {
        $file = $request->files->get('file');
        if (!$file) {
            return new JsonResponse(['error' => 'Brak pliku w polu "file".'], 422);
        }

        $date = (string) $request->request->get('date', '');
        // Akceptuje zarówno RRRR-MM-DD (natywny <input type="date">), jak i RRRR.MM.DD.
        $dateDir = str_replace('-', '.', $date);
        if (!preg_match('/^\d{4}\.\d{2}\.\d{2}$/', $dateDir)) {
            return new JsonResponse(['error' => 'Pole "date" musi być w formacie RRRR-MM-DD.'], 422);
        }

        try {
            $path = $this->input->storeUpload($file, $dateDir);
        } catch (\InvalidArgumentException $e) {
            return new JsonResponse(['error' => $e->getMessage()], 422);
        }

        return new JsonResponse(['path' => $path], 201);
    }

    #[Route('', name: 'api_recordings_delete', methods: ['DELETE'])]
    public function delete(Request $request): JsonResponse
    {
        $path = (string) $request->query->get('path', '');
        if ($path === '' || !str_starts_with($path, 'audio/')) {
            return new JsonResponse(['error' => 'Nieprawidłowa ścieżka.'], 422);
        }

        $deleted = $this->input->delete($path);
        if (!$deleted) {
            return new JsonResponse(['error' => 'Nie znaleziono pliku.'], 404);
        }

        return new JsonResponse(['deleted' => $path]);
    }
}
