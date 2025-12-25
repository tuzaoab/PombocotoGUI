#!/usr/bin/env python3
"""
nc_controller.py
# pra você executar isso apenas coloque no terminal: python3 nc_controller.py --port (porta)--batch comandos.txt
#LINHA 106 PARA MUDAR O TEMPO DE ESPERA!!!!!! (recomendo 3 seg, depende do tempo do seus videos.)
Modos:
  --port PORT         Porta a escutar (default 4444)
  --batch FILE        Envia todos os comandos do FILE quando o cliente conectar.
  --fifo PATH         Usa uma FIFO (named pipe). Qualquer linha escrita na FIFO será enviada ao cliente automaticamente.
  --interactive       Modo interativo: digite comandos ao vivo (default se nada for informado).
  --marker MARKER     Marcar fim de saída esperado (opcional). Por padrão não usado.

Exemplos:
  # interativo (digite comandos, verá saída do remoto)
  python3 nc_controller.py --port 4444 --interactive

  # enviar lista e sair
  python3 nc_controller.py --port 4444 --batch commands.txt

  # ler comandos de uma fifo criada previamente
  mkfifo /tmp/cmdpipe
  python3 nc_controller.py --port 4444 --fifo /tmp/cmdpipe
  # em outro terminal: echo "whoami" > /tmp/cmdpipe
"""

import socket, argparse, threading, sys, os, time

def recv_loop(conn):
    """Imprime tudo que vier do remoto."""
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                print("\n[!] Conexão fechada pelo remoto.")
                break
            # print raw bytes decoded (ignora erros)
            sys.stdout.write(data.decode(errors="ignore"))
            sys.stdout.flush()
    except Exception as e:
        print("\n[!] Erro na recepção:", e)

def send_line(conn, line):
    """Envia uma linha como comando (adiciona newline se necessário)."""
    if not line.endswith("\n"):
        line = line + "\n"
    try:
        conn.sendall(line.encode())
    except BrokenPipeError:
        print("[!] conexão fechada; não foi possível enviar.")

def fifo_watcher(conn, fifo_path):
    """Abre FIFO e envia cada linha escrita para o cliente."""
    # tenta abrir a FIFO para leitura contínua
    while True:
        try:
            with open(fifo_path, "r") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line == "":
                        continue
                    print(f"\n[>] FIFO -> enviando: {line}")
                    send_line(conn, line)
        except Exception as e:
            print(f"[!] Erro lendo FIFO {fifo_path}: {e}")
            time.sleep(1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=4444)
    ap.add_argument("--batch", help="arquivo com comandos (um por linha) a enviar automaticamente")
    ap.add_argument("--fifo", help="caminho para FIFO (named pipe). linhas escritas nela serão enviadas automaticamente")
    ap.add_argument("--interactive", action="store_true", help="modo interativo (digite comandos no teclado)")
    args = ap.parse_args()

    host = "0.0.0.0"
    port = args.port

    if not (args.interactive or args.batch or args.fifo):
        args.interactive = True  # default para interativo

    # informa
    print(f"[+] Aguardando conexão em {host}:{port} ... (Ctrl+C para sair)")

    serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversock.bind((host, port))
    serversock.listen(1)

    conn, addr = serversock.accept()
    print(f"[+] Conectado por {addr[0]}:{addr[1]}.")
    t = threading.Thread(target=recv_loop, args=(conn,), daemon=True)
    t.start()
   
    if args.batch:
        if not os.path.exists(args.batch):
            print(f"[!] Arquivo {args.batch} não existe.")
        else:
            with open(args.batch, "r", encoding="utf-8") as f:
                i = 0
                for line in f:
                    cmd = line.rstrip("\n")
                    if not cmd or cmd.lstrip().startswith("#"):
                        continue
                    i += 1
                    print(f"[>] Batch [{i}] -> enviando: {cmd}")
                    send_line(conn, cmd)
                    time.sleep(3)
            print("[+] Batch enviado. Aguarde as saídas (serão impressas automaticamente).")
            try:
                t.join()
            except KeyboardInterrupt:
                pass
            finally:
                conn.close()
                serversock.close()
                return

    # se fifo: cria watcher em thread
    if args.fifo:
        fifo_path = args.fifo
        if not os.path.exists(fifo_path):
            print(f"[!] FIFO {fifo_path} não existe. Crie com: mkfifo {fifo_path}")
        else:
            fw = threading.Thread(target=fifo_watcher, args=(conn, fifo_path), daemon=True)
            fw.start()
            print(f"[+] Lendo FIFO {fifo_path}. Escreva comandos nela para enviar ao remoto.")

    # modo interativo (enviar o que digitar)
    if args.interactive:
        print("[+] Modo interativo: digite comandos. 'exit' para fechar.")
        try:
            while True:
                try:
                    cmd = input("> ").rstrip("\n")
                except EOFError:
                    break
                if cmd.strip().lower() in ("exit", "quit"):
                    print("[*] Enviando exit e fechando.")
                    send_line(conn, "exit")
                    break
                if cmd.strip() == "":
                    continue
                send_line(conn, cmd)
                # não bloqueamos — recv_loop imprime a resposta quando chegar
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("\n[*] Ctrl+C — fechando.")
        finally:
            try:
                conn.close()
            except:
                pass
            serversock.close()

if __name__ == "__main__":
    main()
