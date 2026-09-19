<?php

namespace App\Service;

use Symfony\Component\DependencyInjection\Attribute\Autowire;
use Symfony\Component\Finder\Finder;
use Symfony\Component\HttpFoundation\File\UploadedFile;

/**
 * Zarządza plikami pod input/audio/ — nagraniami, które
 * scripts/transcribe.py bierze na wejście. Odzwierciedla strukturę
 * "input/audio/RRRR.MM.DD/<nazwa pliku>" używaną przez cały pipeline.
 */
class InputFileManager
{
    private const AUDIO_EXTENSIONS = ['mp3', 'm4a', 'wav', 'mp4', 'aac', 'ogg', 'wma'];

    public function __construct(
        #[Autowire(param: 'app.input_dir')]
        private readonly string $inputDir,
    ) {
    }

    /**
     * @return list<array{date_dir: string, filename: string, path: string, size_bytes: int, modified_at: string}>
     */
    public function scanAudio(): array
    {
        $audioDir = $this->inputDir . '/audio';
        if (!is_dir($audioDir)) {
            return [];
        }

        $finder = new Finder();
        $finder->files()->in($audioDir);

        $results = [];
        foreach ($finder as $file) {
            if (!in_array(strtolower($file->getExtension()), self::AUDIO_EXTENSIONS, true)) {
                continue;
            }
            $relativeDir = trim(str_replace('\\', '/', $file->getRelativePath()), '/');
            $results[] = [
                'date_dir' => $relativeDir,
                'filename' => $file->getFilename(),
                'path' => 'audio/' . ($relativeDir !== '' ? $relativeDir . '/' : '') . $file->getFilename(),
                'size_bytes' => $file->getSize(),
                'modified_at' => (new \DateTimeImmutable())->setTimestamp($file->getMTime())->format(DATE_ATOM),
            ];
        }

        usort($results, fn ($a, $b) => [$b['date_dir'], $b['filename']] <=> [$a['date_dir'], $a['filename']]);

        return $results;
    }

    public function resolvePath(string $relativePath): string
    {
        return $this->inputDir . '/' . ltrim($relativePath, '/');
    }

    /**
     * Zapisuje wgrany plik pod input/audio/{dateDir}/{nazwa}. Zwraca ścieżkę
     * względem input/ (tak samo jak wpisy z scanAudio()).
     */
    public function storeUpload(UploadedFile $file, string $dateDir, ?string $desiredFilename = null): string
    {
        $dateDir = trim($dateDir, '/');
        if (!preg_match('/^\d{4}\.\d{2}\.\d{2}$/', $dateDir)) {
            throw new \InvalidArgumentException('Data musi być w formacie RRRR.MM.DD.');
        }

        $originalName = $desiredFilename ?: $file->getClientOriginalName();
        $safeName = preg_replace('/[^\p{L}\p{N}_.\-]+/u', '_', $originalName) ?: 'nagranie';

        $targetDir = $this->inputDir . '/audio/' . $dateDir;
        if (!is_dir($targetDir)) {
            mkdir($targetDir, 0775, true);
        }

        // Nie nadpisuj istniejącego nagrania — dopisz sufiks, jeśli nazwa już zajęta.
        $finalName = $safeName;
        $counter = 1;
        while (is_file($targetDir . '/' . $finalName)) {
            $pathInfo = pathinfo($safeName);
            $finalName = sprintf('%s_%d.%s', $pathInfo['filename'], $counter++, $pathInfo['extension'] ?? 'mp3');
        }

        $file->move($targetDir, $finalName);

        return 'audio/' . $dateDir . '/' . $finalName;
    }

    public function delete(string $relativePath): bool
    {
        $fullPath = $this->resolvePath($relativePath);
        if (!is_file($fullPath)) {
            return false;
        }
        return unlink($fullPath);
    }
}
