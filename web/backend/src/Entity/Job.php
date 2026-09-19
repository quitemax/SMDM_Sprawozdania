<?php

namespace App\Entity;

use App\Repository\JobRepository;
use Doctrine\DBAL\Types\Types;
use Doctrine\ORM\Mapping as ORM;

/**
 * Zadanie kolejki pipeline'u (Faza 3) — jeden wiersz na jedno uruchomienie
 * jednego skryptu z scripts/ (transcribe.py, identify_speakers.py, ...).
 * Odbierane przez scripts/job_worker.py w kontenerze `app`, który odpytuje
 * tę tabelę i uruchamia dokładnie te same skrypty CLI co dziś ręcznie.
 */
#[ORM\Entity(repositoryClass: JobRepository::class)]
#[ORM\Table(name: 'jobs')]
class Job
{
    public const STATUS_PENDING = 'pending';
    public const STATUS_RUNNING = 'running';
    public const STATUS_SUCCESS = 'success';
    public const STATUS_FAILED = 'failed';

    /** @var list<string> */
    public const TYPES = ['transcribe', 'identify_speakers', 'clean_transcript', 'init_meeting_info', 'generate_report'];

    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column]
    private ?int $id = null;

    #[ORM\Column(length: 32)]
    private string $type;

    #[ORM\Column(length: 16)]
    private string $status = self::STATUS_PENDING;

    /** Argumenty przekazywane workerowi — ścieżki plików względem korzenia repo, patrz job_worker.py. */
    #[ORM\Column(type: Types::JSON)]
    private array $params = [];

    #[ORM\Column(type: Types::TEXT, length: 16777215, options: ['default' => ''])]
    private string $log = '';

    #[ORM\Column(nullable: true)]
    private ?int $exitCode = null;

    #[ORM\Column]
    private \DateTimeImmutable $createdAt;

    #[ORM\Column(nullable: true)]
    private ?\DateTimeImmutable $startedAt = null;

    #[ORM\Column(nullable: true)]
    private ?\DateTimeImmutable $finishedAt = null;

    public function __construct()
    {
        $this->createdAt = new \DateTimeImmutable();
    }

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getType(): string
    {
        return $this->type;
    }

    public function setType(string $type): static
    {
        $this->type = $type;
        return $this;
    }

    public function getStatus(): string
    {
        return $this->status;
    }

    public function setStatus(string $status): static
    {
        $this->status = $status;
        return $this;
    }

    public function getParams(): array
    {
        return $this->params;
    }

    public function setParams(array $params): static
    {
        $this->params = $params;
        return $this;
    }

    public function getLog(): string
    {
        return $this->log;
    }

    public function getExitCode(): ?int
    {
        return $this->exitCode;
    }

    public function getCreatedAt(): \DateTimeImmutable
    {
        return $this->createdAt;
    }

    public function getStartedAt(): ?\DateTimeImmutable
    {
        return $this->startedAt;
    }

    public function getFinishedAt(): ?\DateTimeImmutable
    {
        return $this->finishedAt;
    }

    /** @return array<string, mixed> */
    public function toArray(): array
    {
        return [
            'id' => $this->id,
            'type' => $this->type,
            'status' => $this->status,
            'params' => $this->params,
            'exit_code' => $this->exitCode,
            'created_at' => $this->createdAt->format(DATE_ATOM),
            'started_at' => $this->startedAt?->format(DATE_ATOM),
            'finished_at' => $this->finishedAt?->format(DATE_ATOM),
        ];
    }

    /** @return array<string, mixed> */
    public function toArrayWithLog(): array
    {
        return $this->toArray() + ['log' => $this->log];
    }
}
