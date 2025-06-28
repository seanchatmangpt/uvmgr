# High-performance command execution core
# x86_64 assembly for minimal overhead command dispatch

.global _fast_exec
.global _fast_parse
.global _fast_hash

.text

# Fast command execution with minimal overhead
# rdi: command string pointer
# rsi: command length
# rdx: environment pointer
# Returns: rax = exit code
_fast_exec:
    push rbp
    mov rbp, rsp
    
    # Fast path for common commands
    cmp rsi, 2
    je .check_ls
    cmp rsi, 3
    je .check_pwd
    
    # Standard execution path
    mov rax, 59  # sys_execve
    syscall
    
    pop rbp
    ret

.check_ls:
    # Optimized ls handling
    mov ax, [rdi]
    cmp ax, 0x736c  # "ls"
    jne .standard_exec
    # Direct syscall for directory listing
    mov rax, 217  # sys_getdents64
    syscall
    pop rbp
    ret

.check_pwd:
    # Optimized pwd handling  
    mov ax, [rdi]
    cmp ax, 0x7770  # "pw"
    jne .standard_exec
    mov al, [rdi+2]
    cmp al, 0x64    # "d"
    jne .standard_exec
    # Direct syscall for getcwd
    mov rax, 79   # sys_getcwd
    syscall
    pop rbp
    ret

.standard_exec:
    jmp _fast_exec
