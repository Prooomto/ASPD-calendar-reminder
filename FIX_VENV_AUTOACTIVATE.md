# Как убрать автоматическую активацию venv при запуске терминала

## Проблема
При каждом открытии PowerShell автоматически выполняется команда:
```powershell
& "c:/Users/sseri/OneDrive/Desktop/ASPD calendar-reminder/venv/Scripts/Activate.ps1"
```

## Решение

### Шаг 1: Найдите файл профиля PowerShell

Откройте PowerShell и выполните:
```powershell
notepad $PROFILE
```

Или проверьте путь к профилю:
```powershell
echo $PROFILE
```

Обычно это один из этих файлов:
- `C:\Users\sseri\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`
- `C:\Users\sseri\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`

### Шаг 2: Откройте файл профиля

Если файл не существует, создайте его:
```powershell
if (!(Test-Path -Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force
}
notepad $PROFILE
```

### Шаг 3: Найдите и удалите строку

В открывшемся файле найдите строку, которая содержит:
```powershell
& "c:/Users/sseri/OneDrive/Desktop/ASPD calendar-reminder/venv/Scripts/Activate.ps1"
```

Или похожую строку с путем к `Activate.ps1`. **Удалите эту строку полностью.**

### Шаг 4: Сохраните файл и перезапустите терминал

1. Сохраните файл (Ctrl+S)
2. Закройте все окна PowerShell
3. Откройте новое окно PowerShell
4. Автоматическая активация больше не должна происходить

## Альтернативный способ (быстрый)

Если вы хотите быстро найти и удалить строку, выполните в PowerShell:

```powershell
# Открыть профиль в блокноте
notepad $PROFILE

# Или найти строку с venv
Select-String -Path $PROFILE -Pattern "venv.*Activate"
```

Затем вручную удалите найденную строку.

## Если профиль не существует

Если файл профиля не существует, значит автозапуск настроен где-то еще:

1. Проверьте настройки VS Code (если используете):
   - Файл → Настройки → Settings
   - Поиск: "terminal.integrated.shellArgs.windows"
   - Удалите команду активации venv

2. Проверьте настройки Windows Terminal:
   - Откройте настройки (Ctrl+,)
   - Проверьте раздел "Startup" или "Profiles"
   - Удалите команду активации venv

3. Проверьте переменные окружения:
   ```powershell
   $env:PSModulePath
   ```

## Проверка

После удаления строки, откройте новый терминал PowerShell. Команда активации venv больше не должна выполняться автоматически.


