#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>

static const size_t BUFFER_SIZE = 1024;

#define CMD_NOP 0x0
#define CMD_ECHO 0x1
#define CMD_READ 0x2
#define CMD_WRITE 0x3

int main(int argc, char** argv)
{
    int fd;
    ssize_t received;
    struct sockaddr_in server_addr;
    struct sockaddr_in client_addr;
    socklen_t client_addr_size;
    char buffer[BUFFER_SIZE];
    int kv[BUFFER_SIZE];
    int key;
    int value;

    fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) {
        perror("can't create socket");
        return -1;
    }

    value = 1;
    if (setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &value, sizeof(int)) < 0) {
        perror("setsockopt(SO_REUSEADDR) failed");
        return -1;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    server_addr.sin_port = htons(31337);

    if (bind(fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0){
        perror("cannot bind");
        return -1;
    }

    while (1) {
        received = recvfrom(fd, buffer, BUFFER_SIZE,
                0, (struct sockaddr*)&client_addr, &client_addr_size);
        if (received < 0) {
            perror("failed recvfrom");
        }
        
        if (received == 0 || *(int *)buffer != 0xFFFFFFFF) {
            continue;
        }

        switch (buffer[4]) {
            case CMD_NOP:
                break;
            case CMD_ECHO:
                sendto(fd, &buffer[5], 4, 0,
                        (struct sockaddr*)&client_addr, client_addr_size);
                break;
            case CMD_READ:
                key = *(int *)&buffer[5];
                sendto(fd, &kv[key], 4, 0,
                        (struct sockaddr*)&client_addr, client_addr_size);
                break;
            case CMD_WRITE:
                key = *(int *)&buffer[5];
                value = *(int *)&buffer[9];
                kv[key] = value;
                break;
            default:
                break;
        }
    }

    return 0;
}
