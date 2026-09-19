<?php

namespace App\Controller\Api;

use App\Entity\Job;
use App\Repository\JobRepository;
use App\Service\InputFileManager;
use App\Service\OutputFileManager;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;

/**
 * Kolejka zadań pipeline'u (Faza 3) — zapisuje wiersze do tabeli `jobs`,
 * które scripts/job_worker.py (kontener `app`) odbiera i wykonuje jako
 * dokładnie te same skrypty CLI, które dotąd uruchamiało się ręcznie.
 * Ten kontroler NIE uruchamia niczego sam — tylko wstawia/czyta wiersze.
 */
#[Route('/api/jobs')]
class JobController extends AbstractController
{
    public function __construct(
        private readonly EntityManagerInterface $em,
        private readonly JobRepository $jobs,
        private readonly InputFileManager $input,
        private readonly OutputFileManager $output,
    ) {
    }

    #[Route('', name: 'api_jobs_list', methods: ['GET'])]
    public function list(): JsonResponse
    {
        return new JsonResponse(array_map(fn (Job $j) => $j->toArray(), $this->jobs->findRecent()));
    }

    #[Route('/{id}', name: 'api_jobs_get', methods: ['GET'], requirements: ['id' => '\d+'])]
    public function get(int $id): JsonResponse
    {
        $job = $this->jobs->find($id);
        if (!$job) {
            return new JsonResponse(['error' => 'Nie znaleziono zadania.'], 404);
        }
        return new JsonResponse($job->toArrayWithLog());
    }

    #[Route('', name: 'api_jobs_create', methods: ['POST'])]
    public function create(Request $request): JsonResponse
    {
        $payload = json_decode($request->getContent(), true) ?? [];
        $type = (string) ($payload['type'] ?? '');
        $path = (string) ($payload['path'] ?? '');

        if (!in_array($type, Job::TYPES, true)) {
            return new JsonResponse(['error' => 'Nieznany typ zadania.'], 422);
        }

        try {
            $params = $this->resolveParams($type, $path, $payload['options'] ?? []);
        } catch (\InvalidArgumentException $e) {
            return new JsonResponse(['error' => $e->getMessage()], 422);
        }

        $job = new Job();
        $job->setType($type);
        $job->setParams($params);
        $this->em->persist($job);
        $this->em->flush();

        return new JsonResponse($job->toArray(), 201);
    }

    #[Route('/{id}/retry', name: 'api_jobs_retry', methods: ['POST'], requirements: ['id' => '\d+'])]
    public function retry(int $id): JsonResponse
    {
        $original = $this->jobs->find($id);
        if (!$original) {
            return new JsonResponse(['error' => 'Nie znaleziono zadania.'], 404);
        }

        $job = new Job();
        $job->setType($original->getType());
        $job->setParams($original->getParams());
        $this->em->persist($job);
        $this->em->flush();

        return new JsonResponse($job->toArray(), 201);
    }

    /**
     * Sprawdza, czy plik podany przez UI naprawdę istnieje i pasuje do typu
     * zadania, i zamienia go na argumenty, których oczekuje job_worker.py
     * (ścieżki względem korzenia repo — tak, jak widzi je kontener `app`).
     *
     * @param array<string, mixed> $options
     * @return array<string, mixed>
     */
    private function resolveParams(string $type, string $path, array $options): array
    {
        if ($type === 'transcribe') {
            if (!str_starts_with($path, 'audio/') || !is_file($this->input->resolvePath($path))) {
                throw new \InvalidArgumentException('Nie znaleziono nagrania pod podaną ścieżką.');
            }
            $params = ['audio_path' => 'input/' . $path];
            if (array_key_exists('diarize', $options)) {
                $params['diarize'] = (bool) $options['diarize'];
            }
            foreach (['min_speakers', 'max_speakers'] as $key) {
                if (!empty($options[$key])) {
                    $params[$key] = (int) $options[$key];
                }
            }
            return $params;
        }

        if (in_array($type, ['identify_speakers', 'clean_transcript', 'init_meeting_info'], true)) {
            if (
                !str_starts_with($path, 'transcripts/')
                || !str_ends_with($path, '.json')
                || str_ends_with($path, '.clean.json')
                || str_ends_with($path, '.speakers.json')
                || str_ends_with($path, '.meeting_info.json')
                || !$this->output->exists($path)
            ) {
                throw new \InvalidArgumentException('Nie znaleziono transkrypcji (.json) pod podaną ścieżką.');
            }
            return ['transcript_path' => 'output/' . $path];
        }

        if ($type === 'generate_report') {
            if (!str_starts_with($path, 'transcripts/') || !str_ends_with($path, '.clean.json') || !$this->output->exists($path)) {
                throw new \InvalidArgumentException('Nie znaleziono oczyszczonej transkrypcji (.clean.json) pod podaną ścieżką.');
            }
            return ['clean_transcript_path' => 'output/' . $path];
        }

        throw new \InvalidArgumentException('Nieznany typ zadania.');
    }
}
