<?php

namespace App\Entity;

use App\Repository\MemberRepository;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity(repositoryClass: MemberRepository::class)]
#[ORM\Table(name: 'members')]
class Member
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column]
    private ?int $id = null;

    #[ORM\Column(length: 255)]
    private string $fullName;

    /** Rola, do której osoba jest domyślnie przypisywana przy dodawaniu do nowego spotkania. */
    #[ORM\Column(length: 20)]
    private string $defaultBody = 'rada_nadzorcza';

    #[ORM\Column]
    private bool $active = true;

    /**
     * Etykieta roli używana WYŁĄCZNIE przy eksporcie osób z default_body="inny"
     * do meeting_info.json (np. "radca prawny", "obserwator") — odtwarza
     * format "Imię Nazwisko (rola)", który scripts/generate_report.py już
     * umie parsować (patrz render_attendance()). Puste dla rada_nadzorcza/zarzad.
     */
    #[ORM\Column(length: 100, nullable: true)]
    private ?string $roleLabel = null;

    #[ORM\Column(type: 'text', nullable: true)]
    private ?string $notes = null;

    #[ORM\Column]
    private \DateTimeImmutable $createdAt;

    #[ORM\Column]
    private \DateTimeImmutable $updatedAt;

    public function __construct()
    {
        $this->createdAt = new \DateTimeImmutable();
        $this->updatedAt = new \DateTimeImmutable();
    }

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getFullName(): string
    {
        return $this->fullName;
    }

    public function setFullName(string $fullName): static
    {
        $this->fullName = $fullName;
        return $this;
    }

    public function getDefaultBody(): string
    {
        return $this->defaultBody;
    }

    public function setDefaultBody(string $defaultBody): static
    {
        $this->defaultBody = $defaultBody;
        return $this;
    }

    public function isActive(): bool
    {
        return $this->active;
    }

    public function setActive(bool $active): static
    {
        $this->active = $active;
        return $this;
    }

    public function getRoleLabel(): ?string
    {
        return $this->roleLabel;
    }

    public function setRoleLabel(?string $roleLabel): static
    {
        $this->roleLabel = $roleLabel;
        return $this;
    }

    public function getNotes(): ?string
    {
        return $this->notes;
    }

    public function setNotes(?string $notes): static
    {
        $this->notes = $notes;
        return $this;
    }

    public function getCreatedAt(): \DateTimeImmutable
    {
        return $this->createdAt;
    }

    public function getUpdatedAt(): \DateTimeImmutable
    {
        return $this->updatedAt;
    }

    public function touch(): static
    {
        $this->updatedAt = new \DateTimeImmutable();
        return $this;
    }

    /** @return array<string, mixed> */
    public function toArray(): array
    {
        return [
            'id' => $this->id,
            'full_name' => $this->fullName,
            'default_body' => $this->defaultBody,
            'active' => $this->active,
            'role_label' => $this->roleLabel,
            'notes' => $this->notes,
            'created_at' => $this->createdAt->format(DATE_ATOM),
            'updated_at' => $this->updatedAt->format(DATE_ATOM),
        ];
    }
}
