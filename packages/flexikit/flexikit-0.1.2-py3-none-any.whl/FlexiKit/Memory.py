class Memory:
    """
    A Python wrapper for inter-process memory access using Memorydll.dll.
    """

    def __init__(self, dll_name="Memorydll.dll"):
        """
        Initializes the Memory class and loads the DLL.
        
        Args:
            dll_name (str): The name of the DLL file.
        """
        dll_path = os.path.join(os.path.dirname(__file__), dll_name)

        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"DLL file not found at: {dll_path}")

        try:
            self._memory_dll = ctypes.cdll.LoadLibrary(dll_path)
            self._setup_function_signatures()
        except OSError as e:
            raise RuntimeError(f"Error loading DLL: {e}")
            
        self._h_process = None

    def _setup_function_signatures(self):
        """
        Defines the function prototypes for the C++ DLL functions.
        """
        self._memory_dll.get_process_id.restype = DWORD
        self._memory_dll.get_process_id.argtypes = [ctypes.c_char_p]
        
        self._memory_dll.open_process_by_id.restype = HANDLE
        self._memory_dll.open_process_by_id.argtypes = [DWORD]
        
        self._memory_dll.close_handle.argtypes = [HANDLE]
        
        self._memory_dll.read_process_memory.argtypes = [HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
        
        self._memory_dll.write_process_memory.argtypes = [HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_process()

    def open_process(self, process_name: str):
        """Finds and opens a process by name."""
        pid = self._memory_dll.get_process_id(process_name.encode('utf-8'))
        if pid == 0:
            raise ValueError(f"Process '{process_name}' not found.")
        
        self._h_process = self._memory_dll.open_process_by_id(pid)
        if not self._h_process:
            raise RuntimeError("Could not open process. Try running as administrator.")
        print(f"Successfully attached to PID {pid}")

    def close_process(self):
        """Closes the currently opened process handle."""
        if self._h_process:
            self._memory_dll.close_handle(self._h_process)
            self._h_process = None
            print("Process handle closed.")

    def read_memory(self, address: int, size: int) -> bytes:
        """
        Reads a specified number of bytes from a memory address in the target process.

        Args:
            address (int): The memory address to read from.
            size (int): The number of bytes to read.

        Returns:
            bytes: The raw data read from memory.
        """
        if not self._h_process:
            raise RuntimeError("No process is open.")
        buffer = ctypes.create_string_buffer(size)
        try:
            self._memory_dll.read_process_memory(self._h_process, ctypes.c_void_p(address), ctypes.byref(buffer), size)
            return buffer.raw
        except OSError as e:
            raise OSError(f"Error reading memory at address {hex(address)}: {e}")

    def write_memory(self, address: int, data: bytes):
        """
        Writes a block of bytes to a specified memory address in the target process.

        Args:
            address (int): The memory address to write to.
            data (bytes): The data to write.
        """
        if not self._h_process:
            raise RuntimeError("No process is open.")
        if not isinstance(data, bytes):
            raise TypeError("Data must be a bytes object.")
        
        buffer = ctypes.create_string_buffer(data, len(data))
        try:
            self._memory_dll.write_process_memory(self._h_process, ctypes.c_void_p(address), ctypes.byref(buffer), len(data))
        except OSError as e:
            raise OSError(f"Error writing memory at address {hex(address)}: {e}")

    def read_int(self, address: int) -> int:
        """Reads a 4-byte signed integer from a memory address."""
        data = self.read_memory(address, ctypes.sizeof(ctypes.c_int))
        return int.from_bytes(data, 'little', signed=True)
    
    def write_int(self, address: int, value: int):
        """Writes a 4-byte signed integer to a memory address."""
        data = value.to_bytes(ctypes.sizeof(ctypes.c_int), 'little', signed=True)
        self.write_memory(address, data)

    def read_float(self, address: int) -> float:
        """Reads a 4-byte float from a memory address."""
        data = self.read_memory(address, ctypes.sizeof(ctypes.c_float))
        return ctypes.c_float.from_buffer_copy(data).value

    def write_float(self, address: int, value: float):
        """Writes a 4-byte float to a memory address."""
        self.write_memory(address, ctypes.c_float(value))

# --- Example Usage for Notepad.exe ---
if __name__ == '__main__':
    # You must have Notepad.exe running for this example to work.
    # Run this script as an administrator for proper access.
    try:
        with Memory() as mem:
            mem.open_process("notepad.exe")
            print("Attached to Notepad.exe. Remember to run as an Administrator.")

            # This is not a reliable way to find Notepad's memory, as memory addresses are dynamic.
            # This is for demonstration purposes only.
            # In a real scenario, you'd find a specific memory address using a debugger or memory scanner.
            # Hypothetical memory address (replace with a real address if you know one)
            hypothetical_address = 0x00000000185c1840

            print(f"Attempting to write a new string to hypothetical address {hex(hypothetical_address)}...")
            new_string = b"Python is cool!\x00"  # Null-terminated string
            mem.write_memory(hypothetical_address, new_string)
            print("Write successful.")

            print("Attempting to read back from the same address...")
            read_data = mem.read_memory(hypothetical_address, len(new_string))
            print(f"Data read: {read_data.decode('utf-8')}")
            
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as e:
        print(f"An error occurred: {e}")
    finally:
        print("\nExample finished.")
