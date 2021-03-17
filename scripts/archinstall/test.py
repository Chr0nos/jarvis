from arch.archinstall import FileFromHost, File

if __name__ == "__main__":
    custom_servers = [
        'http://192.168.2.3:8080'
    ]

    mirrors = FileFromHost('/dev/shm/mirrorlist', '/')
    mirrors.insert(File.to_config(custom_servers, prepend='Server '), line_index=3)
