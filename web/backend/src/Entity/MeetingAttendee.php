<?php

namespace App\Entity;

use App\Repository\MeetingAttendeeRepository;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity(repositoryClass: MeetingAttendeeRepository::class)]
#[ORM\Table(name: 'meeting_attendees')]
#[ORM\UniqueConstraint(name: 'uniq_meeting_member', columns: ['meeting_id', 'member_id'])]
class MeetingAttendee
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column]
    private ?int $id = null;

    #[ORM\ManyToOne(targetEntity: Meeting::class, inversedBy: 'attendees')]
    #[ORM\JoinColumn(nullable: false, onDelete: 'CASCADE')]
    private Meeting $meeting;

    #[ORM\ManyToOne(targetEntity: Member::class)]
    #[ORM\JoinColumn(nullable: false, onDelete: 'CASCADE')]
    private Member $member;

    /** rada_nadzorcza | zarzad | inny — jaką rolę pełnił NA TYM konkretnym spotkaniu. */
    #[ORM\Column(length: 20)]
    private string $body;

    /** protokolant | sekretarz | przewodniczacy, albo null jeśli zwykły uczestnik. */
    #[ORM\Column(length: 20, nullable: true)]
    private ?string $role = null;

    /**
     * Funkcja/tytuł osoby TAK, JAK BYŁ NA TYM KONKRETNYM SPOTKANIU (np.
     * "Przewodniczący Rady Nadzorczej", "Członek Rady Nadzorczej delegowany
     * do czasowego pełnienia funkcji Członka Zarządu"). Zapisywane jako
     * niezależna kopia przy zapisie formularza — celowo NIE jest to odczyt
     * na żywo z Member::roleLabel, bo funkcja danej osoby (zwłaszcza
     * delegacje) zmienia się w czasie, a stare spotkanie ma pokazywać stan
     * z dnia, w którym się odbyło, niezależnie od późniejszych zmian składu.
     */
    #[ORM\Column(length: 150, nullable: true)]
    private ?string $roleLabel = null;

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getMeeting(): Meeting
    {
        return $this->meeting;
    }

    public function setMeeting(Meeting $meeting): static
    {
        $this->meeting = $meeting;
        return $this;
    }

    public function getMember(): Member
    {
        return $this->member;
    }

    public function setMember(Member $member): static
    {
        $this->member = $member;
        return $this;
    }

    public function getBody(): string
    {
        return $this->body;
    }

    public function setBody(string $body): static
    {
        $this->body = $body;
        return $this;
    }

    public function getRole(): ?string
    {
        return $this->role;
    }

    public function setRole(?string $role): static
    {
        $this->role = $role;
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

    /** @return array<string, mixed> */
    public function toArray(): array
    {
        return [
            'id' => $this->id,
            'member_id' => $this->member->getId(),
            'full_name' => $this->member->getFullName(),
            'body' => $this->body,
            'role' => $this->role,
            'role_label' => $this->roleLabel,
        ];
    }
}
