const std = @import("std");
const learner = @import("learner");

test "chapter contract" {
    if (!learner.implemented) return error.SkipZigTest;
    // TODO: add assertions for this chapter's completion criteria
    return error.MissingContractTests;
}
