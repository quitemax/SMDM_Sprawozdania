<?php

namespace App\Service;

use PhpOffice\PhpWord\Element\AbstractContainer;
use PhpOffice\PhpWord\PhpWord;

/**
 * Zamienia projekt sprawozdania (Markdown ze scripts/generate_report.py) na
 * dokument .docx do pobrania — historyczne protokoły tej spółdzielni są w
 * Wordzie, więc to naturalny format do dalszej redakcji/archiwizacji.
 *
 * To NIE jest ogólny parser Markdown — obsługuje dokładnie ten wąski zestaw
 * składni, który generate_report.py faktycznie produkuje (patrz
 * render_report()/render_attendance()/render_resolutions()): nagłówek `#`,
 * cytat `>` na początku, całe linie **pogrubione** jako pseudo-nagłówki,
 * wypunktowania `- `, sygnatura w pojedynczych gwiazdkach, zwykłe akapity —
 * plus pogrubienia **w środku** dowolnej z tych linii.
 */
class ReportDocxRenderer
{
    public function render(string $markdown): PhpWord
    {
        $phpWord = new PhpWord();
        $phpWord->setDefaultFontName('Calibri');
        $phpWord->setDefaultFontSize(11);

        $section = $phpWord->addSection();
        $lines = preg_split('/\r\n|\r|\n/', $markdown);
        $count = count($lines);

        for ($i = 0; $i < $count; $i++) {
            $line = rtrim($lines[$i]);
            if ($line === '') {
                continue;
            }

            if (str_starts_with($line, '# ')) {
                $section->addTitle($this->stripBold(substr($line, 2)), 1);
                continue;
            }

            if (str_starts_with($line, '>')) {
                $quoteParts = [];
                while ($i < $count && str_starts_with(rtrim($lines[$i]), '>')) {
                    $text = trim(substr(rtrim($lines[$i]), 1));
                    if ($text !== '') {
                        $quoteParts[] = $text;
                    }
                    $i++;
                }
                $i--; // pętla for i tak zrobi ++
                $run = $section->addTextRun(['spaceAfter' => 200]);
                $this->addInlineRuns($run, implode(' ', $quoteParts), ['italic' => true, 'color' => '595959']);
                continue;
            }

            if (str_starts_with($line, '- ')) {
                $run = $section->addListItemRun(0);
                $this->addInlineRuns($run, substr($line, 2));
                continue;
            }

            if (preg_match('/^\*(?!\*)(.+)(?<!\*)\*$/u', $line, $m)) {
                $run = $section->addTextRun();
                $this->addInlineRuns($run, $m[1], ['italic' => true]);
                continue;
            }

            $run = $section->addTextRun(['spaceAfter' => 160]);
            $this->addInlineRuns($run, $line);
        }

        return $phpWord;
    }

    /** @param array<string, mixed> $baseStyle */
    private function addInlineRuns(AbstractContainer $run, string $text, array $baseStyle = []): void
    {
        $parts = preg_split('/(\*\*.+?\*\*)/u', $text, -1, PREG_SPLIT_DELIM_CAPTURE | PREG_SPLIT_NO_EMPTY);
        foreach ($parts as $part) {
            if (str_starts_with($part, '**') && str_ends_with($part, '**') && mb_strlen($part) > 4) {
                $run->addText(mb_substr($part, 2, -2), $baseStyle + ['bold' => true]);
            } else {
                $run->addText($part, $baseStyle);
            }
        }
    }

    private function stripBold(string $text): string
    {
        return trim(str_replace('**', '', $text));
    }
}
