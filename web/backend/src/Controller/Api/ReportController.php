<?php

namespace App\Controller\Api;

use App\Repository\MeetingRepository;
use App\Service\OutputFileManager;
use App\Service\ReportDocxRenderer;
use PhpOffice\PhpWord\Writer\Word2007;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\BinaryFileResponse;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\ResponseHeaderBag;
use Symfony\Component\Routing\Attribute\Route;

/**
 * Podgląd i eksport projektu sprawozdania (scripts/generate_report.py) —
 * Faza 4. Samo (re)generowanie idzie przez kolejkę zadań (JobController,
 * typ "generate_report"), ten kontroler tylko czyta gotowy plik z dysku
 * i, na żądanie, renderuje go do .docx (ReportDocxRenderer).
 */
#[Route('/api/meetings/{id}/report')]
class ReportController extends AbstractController
{
    public function __construct(
        private readonly MeetingRepository $meetings,
        private readonly OutputFileManager $output,
        private readonly ReportDocxRenderer $docxRenderer,
    ) {
    }

    #[Route('', name: 'api_meetings_report_get', methods: ['GET'])]
    public function get(int $id): JsonResponse
    {
        $meeting = $this->meetings->find($id);
        if (!$meeting) {
            return new JsonResponse(['error' => 'Nie znaleziono spotkania.'], 404);
        }

        $reportPath = $this->reportPath($meeting->getTranscriptDir(), $meeting->getName());
        $exists = $this->output->exists($reportPath);

        return new JsonResponse([
            'exists' => $exists,
            'markdown' => $exists ? $this->output->readText($reportPath) : null,
            'report_path' => $reportPath,
            'clean_transcript_path' => sprintf('transcripts/%s/%s.clean.json', $meeting->getTranscriptDir(), $meeting->getName()),
            'generated_at' => $exists
                ? (new \DateTimeImmutable())->setTimestamp(filemtime($this->output->resolvePath($reportPath)))->format(DATE_ATOM)
                : null,
        ]);
    }

    #[Route('/docx', name: 'api_meetings_report_docx', methods: ['GET'])]
    public function docx(int $id): BinaryFileResponse|JsonResponse
    {
        $meeting = $this->meetings->find($id);
        if (!$meeting) {
            return new JsonResponse(['error' => 'Nie znaleziono spotkania.'], 404);
        }

        $reportPath = $this->reportPath($meeting->getTranscriptDir(), $meeting->getName());
        $markdown = $this->output->readText($reportPath);
        if ($markdown === null) {
            return new JsonResponse(['error' => 'Brak wygenerowanego projektu sprawozdania — najpierw je wygeneruj.'], 404);
        }

        $phpWord = $this->docxRenderer->render($markdown);
        $tmpPath = sys_get_temp_dir() . '/smdm_report_' . bin2hex(random_bytes(8)) . '.docx';
        (new Word2007($phpWord))->save($tmpPath);

        $response = new BinaryFileResponse($tmpPath);
        $response->setContentDisposition(
            ResponseHeaderBag::DISPOSITION_ATTACHMENT,
            sprintf('%s_%s.docx', $meeting->getTranscriptDir(), $meeting->getName())
        );
        $response->headers->set('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
        $response->deleteFileAfterSend(true);

        return $response;
    }

    private function reportPath(string $transcriptDir, string $name): string
    {
        return sprintf('reports/%s/%s.draft.md', $transcriptDir, $name);
    }
}
