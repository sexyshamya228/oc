import ctypes                       # Для вызова функций Windows API
import ctypes.wintypes as wt        # Стандартные типы данных Windows


# Подключение необходимых DLL

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # Основная библиотека Windows API
advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)  # Для функций безопасности, имени пользователя
psapi     = ctypes.WinDLL("Psapi.dll", use_last_error=True)    # Для производительности и Pagefile
ntdll     = ctypes.WinDLL("ntdll.dll", use_last_error=True)    # Для реальной версии ОС через RtlGetVersion


# Структура для хранения версии Windows
class RTL_OSVERSIONINFOW(ctypes.Structure):
    _fields_ = [
        ("dwOSVersionInfoSize", wt.DWORD),      # Размер структуры
        ("dwMajorVersion", wt.DWORD),           # Главная версия Windows
        ("dwMinorVersion", wt.DWORD),           # Минорная версия
        ("dwBuildNumber", wt.DWORD),            # Номер сборки
        ("szCSDVersion", wt.WCHAR * 128),       # Строка с информацией о сервис-паке
    ]

def get_real_os_version():
    """Возвращает версию ОС через RtlGetVersion"""
    v = RTL_OSVERSIONINFOW()
    v.dwOSVersionInfoSize = ctypes.sizeof(v)  # Указываем размер структуры
    ntdll.RtlGetVersion(ctypes.byref(v))      # Вызываем функцию из ntdll.dll
    return f"Windows {v.dwMajorVersion}"


def get_user():
    buf = ctypes.create_unicode_buffer(255)  # Буфер для хранения имени
    size = wt.DWORD(255)                     # Размер буфера
    advapi32.GetUserNameW(buf, ctypes.byref(size))  # Вызываем GetUserNameW
    return buf.value

def get_computer():
    buf = ctypes.create_unicode_buffer(255)
    size = wt.DWORD(255)
    kernel32.GetComputerNameW(buf, ctypes.byref(size))  # Вызываем GetComputerNameW
    return buf.value


# Структура для информации о процессоре
class SYSTEM_INFO(ctypes.Structure):
    _fields_ = [
        ("wProcessorArchitecture", wt.WORD),   # Архитектура CPU (x86/x64/ARM)
        ("wReserved", wt.WORD),                 # Зарезервировано
        ("dwPageSize", wt.DWORD),               # Размер страницы памяти
        ("lpMinimumApplicationAddress", wt.LPVOID), # Минимальный адрес приложения
        ("lpMaximumApplicationAddress", wt.LPVOID), # Максимальный адрес приложения
        ("dwActiveProcessorMask", ctypes.POINTER(wt.DWORD)), # Маска активных процессоров
        ("dwNumberOfProcessors", wt.DWORD),    # Количество логических процессоров
        ("dwProcessorType", wt.DWORD),         # Тип процессора
        ("dwAllocationGranularity", wt.DWORD), # Гранулярность выделения памяти
        ("wProcessorLevel", wt.WORD),          # Уровень процессора
        ("wProcessorRevision", wt.WORD),       # Ревизия процессора
    ]

def get_cpu():
    si = SYSTEM_INFO()
    kernel32.GetNativeSystemInfo(ctypes.byref(si))  # Получаем реальную системную информацию
    arch = {
        9: "x64 (AMD64)",
        0: "x86 (32-bit)",
        5: "ARM",
        12: "ARM64",
    }.get(si.wProcessorArchitecture, "Unknown")  # Преобразуем код архитектуры в строку
    return arch, si.dwNumberOfProcessors


# Структура для информации о памяти
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wt.DWORD),            # Размер структуры
        ("dwMemoryLoad", wt.DWORD),        # Процент использования памяти
        ("ullTotalPhys", ctypes.c_ulonglong),    # Общий объём физической памяти
        ("ullAvailPhys", ctypes.c_ulonglong),    # Доступная физическая память
        ("ullTotalPageFile", ctypes.c_ulonglong), # Общий объём файла подкачки
        ("ullAvailPageFile", ctypes.c_ulonglong), # Доступный объём файла подкачки
        ("ullTotalVirtual", ctypes.c_ulonglong),  # Общий объём виртуальной памяти
        ("ullAvailVirtual", ctypes.c_ulonglong),  # Доступный объём виртуальной памяти
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong), # Доп. виртуальная память
    ]

def mem():
    m = MEMORYSTATUSEX()
    m.dwLength = ctypes.sizeof(m)
    kernel32.GlobalMemoryStatusEx(ctypes.byref(m))  # Вызываем функцию Windows API
    return m

# Структура для Pagefile
class PERFORMANCE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("cb", wt.DWORD),
        ("CommitTotal", ctypes.c_size_t),
        ("CommitLimit", ctypes.c_size_t),
        ("CommitPeak", ctypes.c_size_t),
        ("PhysicalTotal", ctypes.c_size_t),
        ("PhysicalAvailable", ctypes.c_size_t),
        ("SystemCache", ctypes.c_size_t),
        ("KernelTotal", ctypes.c_size_t),
        ("KernelPaged", ctypes.c_size_t),
        ("KernelNonpaged", ctypes.c_size_t),
        ("PageSize", ctypes.c_size_t),
        ("HandleCount", wt.DWORD),
        ("ProcessCount", wt.DWORD),
        ("ThreadCount", wt.DWORD),
    ]

def pagefile():
    """Возвращает размер файла подкачки"""
    pi = PERFORMANCE_INFORMATION()
    pi.cb = ctypes.sizeof(pi)
    psapi.GetPerformanceInfo(ctypes.byref(pi), pi.cb)
    return pi


def filesystem_of_drive(drive):
    buf = ctypes.create_unicode_buffer(32)
    kernel32.GetVolumeInformationW(drive, None, 0, None, None, None, buf, 32)
    return buf.value if buf.value else "Unknown"

def print_drives_all():
    print("Drives:")
    drive_bits = kernel32.GetLogicalDrives()  # Получаем маску всех доступных дисков
    for i in range(26):  # Перебираем диски A-Z
        if drive_bits & (1 << i):  # Проверяем, есть ли диск
            drive_letter = chr(65 + i) + ":\\"  # Преобразуем индекс в букву диска
            free = wt.ULARGE_INTEGER()
            total = wt.ULARGE_INTEGER()
            try:
                # Получаем свободное и общее место на диске
                kernel32.GetDiskFreeSpaceExW(drive_letter, ctypes.byref(free), ctypes.byref(total), None)
                fs_type = filesystem_of_drive(drive_letter)  # Тип файловой системы
                print(f"  - {drive_letter} ({fs_type}): {free.value // (1024**3)} GB free / {total.value // (1024**3)} GB total")
            except Exception:
                print(f"  - {drive_letter} (Unknown): cannot access")
    print()



"""Вывод всей информации"""
m = mem()            
pf = pagefile()      
mb = lambda x: x // (1024 * 1024) 
arch, cpus = get_cpu()

print(f"OS: {get_real_os_version()}")
print(f"Computer Name: {get_computer()}")
print(f"User: {get_user()}")
print(f"Architecture: {arch}")
print(f"RAM: {mb(m.ullTotalPhys - m.ullAvailPhys)}MB / {mb(m.ullTotalPhys)}MB")
print(f"Virtual Memory: {mb(m.ullTotalVirtual)}MB")
print(f"Memory Load: {m.dwMemoryLoad}%")
print(f"Pagefile: {(pf.CommitTotal * pf.PageSize)//(1024**2)}MB / {(pf.CommitLimit * pf.PageSize)//(1024**2)}MB\n")
print(f"Processors: {cpus}")
print_drives_all() 


