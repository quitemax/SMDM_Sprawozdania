<?php

namespace App\Service;

use Symfony\Component\DependencyInjection\Attribute\Autowire;
use Symfony\Component\Finder\Finder;

/**
 * Czyta i zapisuje <nazwa>.meeting_info.json na dysku — dokładnie ten sam
 * format, który tworzy scripts/init_meeting_info.py i czyta
 * scripts/generate_report.py. Plik na dysku jest źródłem prawdy (patrz
 * decyzja projektowa w docs/PROJECT_MEMORY.md / plan Kroku 2) — ta klasa
 * nigdy nie trzyma stanu poza tym, co właśnie przeczytała/zapisała.
 */
class MeetingInfoFileManager
{
    public function __construct(
        #[Autowire(param: 'app.output_dir')]
        private readonly string $outputDir,
    ) {
    }

    /**
     * Znajduje wszystkie *.meeting_info.json pod output/transcripts/.
     *
     * @return list<array{transcript_dir: string, name: string, path: string}>
     */
    public function scan(): array
    {
        $transcriptsDir = $this->outputDir . '/transcripts';
        if (!is_dir($transcriptsDir)) {
            return [];
        }

        $finder = new Finder();
        $finder->files()->in($transcriptsDir)->name('*.meeting_info.json');

        $results = [];
        foreach ($finder as $file) {
            $relativeDir = trim(str_replace('\\', '/', $file->getRelativePath()), '/');
            $name = preg_replace('/\.meeting_info\.json$/', '', $file->getFilename());
            $results[] = [
                'transcript_dir' => $relativeDir,
                'name' => $name,
                'path' => 'transcripts/' . ($relativeDir !== '' ? $relativeDir . '/' : '') . $file->getFilename(),
            ];
        }

        return $results;
    }

    /** @return array<string, mixed>|null */
    public function read(string $relativePath): ?array
    {
        $fullPath = $this->outputDir . '/' . ltrim($relativePath, '/');
        if (!is_file($fullPath)) {
            return null;
        }

        $decoded = json_decode(file_get_contents($fullPath), true);
        return is_array($decoded) ? $decoded : null;
    }

    /** @param array<string, mixed> $data */
    public function write(string $relativePath, array $data): void
    {
        $fullPath = $this->outputDir . '/' . ltrim($relativePath, '/');
        $dir = dirname($fullPath);
        if (!is_dir($dir)) {
            mkdir($dir, 0775, true);
        }

        file_put_contents(
            $fullPath,
            json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n"
        );
    }
}
