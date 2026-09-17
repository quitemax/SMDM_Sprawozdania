<?php

namespace App\Entity;

use App\Repository\MeetingRepository;
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

/**
 * Indeks spotkań do UI — odzwierciedla to, co faktycznie jest na dysku pod
 * output/transcripts/<data>/<nazwa>.meeting_info.json (patrz
 * scripts/init_meeting_info.py). Plik na dysku pozostaje źródłem prawdy dla
 * treści meeting_info — ten wiersz to tylko wskaźnik + skrót danych do
 * wyświetlenia w UI, odświeżany przy skanowaniu i przy każdym zapisie z UI.
 */
#[ORM\Entity(repositoryClass: MeetingRepository::class)]
#[ORM\Table(name: 'meetings')]
#[ORM\UniqueConstraint(name: 'uniq_transcript_dir_name', columns: ['transcript_dir', 'name'])]
class Meeting
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column]
    private ?int $id = null;

    #[ORM\Column(type: 'date_immutable', nullable: true)]
    private ?\DateTimeImmutable $meetingDate = null;

    /** Nazwa pliku transkrypcji (bez rozszerzenia), np. "10.08.2026". */
    #[ORM\Column(length: 255)]
    private string $name;

    /** Ścieżka katalogu względem output/transcripts/, np. "2026.08.10". */
    #[ORM\Column(length: 255)]
    private string $transcriptDir;

    #[ORM\Column(length: 50, nullable: true)]
    private ?string $protocolNumber = null;

    /** Pełna ścieżka do <nazwa>.meeting_info.json względem katalogu output/. */
    #[ORM\Column(length: 500)]
    private string $meetingInfoPath;

    #[ORM\OneToMany(mappedBy: 'meeting', targetEntity: MeetingAttendee::class, cascade: ['persist', 'remove'], orphanRemoval: true)]
    private Collection $attendees;

    #[ORM\Column]
    private \DateTimeImmutable $createdAt;

    #[ORM\Column]
    private \DateTimeImmutable $updatedAt;

    public function __construct()
    {
        $this->attendees = new ArrayCollection();
        $this->createdAt = new \DateTimeImmutable();
        $this->updatedAt = new \DateTimeImmutable();
    }

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getMeetingDate(): ?\DateTimeImmutable
    {
        return $this->meetingDate;
    }

    public function setMeetingDate(?\DateTimeImmutable $meetingDate): static
    {
        $this->meetingDate = $meetingDate;
        return $this;
    }

    public function getName(): string
    {
        return $this->name;
    }

    public function setName(string $name): static
    {
        $this->name = $name;
        return $this;
    }

    public function getTranscriptDir(): string
    {
        return $this->transcriptDir;
    }

    public function setTranscriptDir(string $transcriptDir): static
    {
        $this->transcriptDir = $transcriptDir;
        return $this;
    }

    public function getProtocolNumber(): ?string
    {
        return $this->protocolNumber;
    }

    public function setProtocolNumber(?string $protocolNumber): static
    {
        $this->protocolNumber = $protocolNumber;
        return $this;
    }

    public function getMeetingInfoPath(): string
    {
        return $this->meetingInfoPath;
    }

    public function setMeetingInfoPath(string $meetingInfoPath): static
    {
        $this->meetingInfoPath = $meetingInfoPath;
        return $this;
    }

    /** @return Collection<int, MeetingAttendee> */
    public function getAttendees(): Collection
    {
        return $this->attendees;
    }

    public function addAttendee(MeetingAttendee $attendee): static
    {
        if (!$this->attendees->contains($attendee)) {
            $this->attendees->add($attendee);
            $attendee->setMeeting($this);
        }
        return $this;
    }

    public function removeAttendee(MeetingAttendee $attendee): static
    {
        $this->attendees->removeElement($attendee);
        return $this;
    }

    public function clearAttendees(): static
    {
        $this->attendees->clear();
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
            'meeting_date' => $this->meetingDate?->format('Y-m-d'),
            'name' => $this->name,
            'transcript_dir' => $this->transcriptDir,
            'protocol_number' => $this->protocolNumber,
            'meeting_info_path' => $this->meetingInfoPath,
            'created_at' => $this->createdAt->format(DATE_ATOM),
            'updated_at' => $this->updatedAt->format(DATE_ATOM),
        ];
    }
}
