<?php

namespace App\Service;

use Symfony\Component\DependencyInjection\Attribute\Autowire;
use Symfony\Component\Finder\Finder;

/**
 * Czyta i zapisuje pliki pod output/ (transkrypcje, meeting_info.json,
 * speakers.json, próbki audio mówców) — dokładnie te same pliki, które
 * tworzą i czytają scripts/*.py. Pliki na dysku są źródłem prawdy (patrz
 * decyzja projektowa w docs/PROJECT_MEMORY.md / plan Kroku 2) — ta klasa
 * nigdy nie trzyma stanu poza tym, co właśnie przeczytała/zapisała.
 */
class OutputFileManager
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

    public function resolvePath(string $relativePath): string
    {
        return $this->outputDir . '/' . ltrim($relativePath, '/');
    }

    public function exists(string $relativePath): bool
    {
        return is_file($this->resolvePath($relativePath));
    }

    /** @return array<string, mixed>|null */
    public function read(string $relativePath): ?array
    {
        $fullPath = $this->resolvePath($relativePath);
        if (!is_file($fullPath)) {
            return null;
        }

        $decoded = json_decode(file_get_contents($fullPath), true);
        return is_array($decoded) ? $decoded : null;
    }

    public function readText(string $relativePath): ?string
    {
        $fullPath = $this->resolvePath($relativePath);
        return is_file($fullPath) ? file_get_contents($fullPath) : null;
    }

    /** @param array<string, mixed> $data */
    public function write(string $relativePath, array $data): void
    {
        $fullPath = $this->resolvePath($relativePath);
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
