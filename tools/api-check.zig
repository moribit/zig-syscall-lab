const std = @import("std");
const builtin = @import("builtin");

// Declaration probes only; this is not a chapter implementation.
test "0.17 declarations used by guides" {
    comptime {
        _ = @TypeOf(std.posix.read);
        _ = @TypeOf(std.posix.openat);
        _ = @TypeOf(std.posix.poll);
        _ = @TypeOf(std.Io.async);
        _ = @TypeOf(std.Io.concurrent);
        _ = @TypeOf(std.Io.Future(void).await);
        _ = @TypeOf(std.Io.Future(void).cancel);
        _ = @TypeOf(std.Io.Group.async);
        _ = @TypeOf(std.Io.Group.concurrent);
        _ = @TypeOf(std.Io.Group.await);
        _ = @TypeOf(std.Io.Group.cancel);
        _ = @TypeOf(std.Io.Threaded.init);
        _ = @TypeOf(std.Io.Threaded.io);
        _ = @TypeOf(std.Io.Threaded.deinit);
        _ = @TypeOf(std.Io.sleep);
        _ = @TypeOf(std.Thread.getCurrentId);
        if (!@hasField(std.process.Init, "io")) @compileError("missing init.io");
        if (builtin.os.tag == .linux) {
            const linux = std.os.linux;
            _ = @TypeOf(linux.write);
            _ = @TypeOf(linux.close);
            _ = @TypeOf(linux.socket);
            _ = @TypeOf(linux.accept4);
            _ = @TypeOf(linux.epoll_create1);
            _ = @TypeOf(linux.epoll_ctl);
            _ = @TypeOf(linux.epoll_wait);
            _ = @TypeOf(linux.eventfd);
            _ = @TypeOf(linux.io_uring_setup);
            _ = @TypeOf(linux.io_uring_enter);
            _ = @TypeOf(linux.IoUring.read);
            _ = @TypeOf(linux.IoUring.write);
            _ = @TypeOf(linux.IoUring.accept);
            _ = @TypeOf(linux.IoUring.recv);
            _ = @TypeOf(linux.IoUring.send);
            _ = @TypeOf(linux.IoUring.cancel);
        }
    }
}
