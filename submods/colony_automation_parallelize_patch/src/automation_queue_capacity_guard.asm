bits 64
default rel

org 0x1423b4700

resolve_planet_reference equ 0x140d464b0
queue_registry          equ 0x1432876d8

; RCX: colony
; AL: 1 when all native construction slots are occupied, otherwise 0
automation_queue_capacity_guard:
    sub rsp, 0x28

    mov rcx, [rcx + 0xf78]
    call resolve_planet_reference
    mov eax, [rax + 0xc4]

    ; Flat binaries have no relocation table. Encode a true RIP-relative load.
    db 0x48, 0x8b, 0x15
    dd queue_registry - ($ + 4)
    test rdx, rdx
    jz .invalid_queue

    mov r8d, eax
    and r8d, 0x00ffffff
    cmp r8d, [rdx + 0x20]
    jae .invalid_queue

    mov rdx, [rdx + 0x18]
    mov r9d, r8d
    shl r9, 4
    mov rdx, [rdx + r9 + 8]
    test rdx, rdx
    jz .invalid_queue
    cmp [rdx + 8], eax
    jne .invalid_queue

    mov ecx, [rdx + 0x2c]
    cmp ecx, [rdx + 0x48]
    setge al
    add rsp, 0x28
    ret

.invalid_queue:
    xor eax, eax
    add rsp, 0x28
    ret
