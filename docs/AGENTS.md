# Instrukcje dla agentów AI

## Cel

Ten dokument zawiera zasady, których powinien przestrzegać agent AI
pracujący nad projektem.

## Język

- Dokumentacja przeznaczona dla pracowników powinna być pisana po polsku.
- Interfejs użytkownika powinien być w języku polskim, o ile nie ustalono inaczej.
- Kod źródłowy, nazwy funkcji, zmiennych i plików mogą być pisane po angielsku.
- Komentarze w kodzie powinny być krótkie i rzeczowe.

## Dane poufne

Nagrania spotkań, transkrypcje i raporty mogą zawierać informacje poufne.

Agent nie powinien:

- przesyłać danych spotkań do zewnętrznych usług bez wyraźnej zgody,
- umieszczać danych osobowych w kodzie źródłowym,
- dodawać rzeczywistych nagrań lub raportów do repozytorium Git,
- publikować poufnych danych w logach lub komunikatach błędów.

## Dokumentacja

Po wprowadzeniu istotnej zmiany należy sprawdzić, czy wymaga ona:

- aktualizacji `README.md`,
- aktualizacji `docs/INSTALLATION.md`,
- wpisu w `docs/HISTORY.md`,
- wpisu w `docs/PROJECT_MEMORY.md`.

## Zasady zmian

Nie należy zmieniać działającej konfiguracji bez sprawdzenia,
jakie inne elementy projektu mogą od niej zależeć.

W przypadku problemów z zależnościami należy zapisać:

- wersję problematycznego pakietu,
- komunikat błędu,
- zastosowane rozwiązanie,
- wynik testu po rozwiązaniu problemu.

## Reprodukowalność

Każda istotna zależność projektu powinna mieć określoną wersję
lub zakres wersji umożliwiający odtworzenie środowiska na innym komputerze.