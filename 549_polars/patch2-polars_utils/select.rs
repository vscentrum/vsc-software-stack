pub fn select_unpredictable<T>(cond: bool, true_val: T, false_val: T) -> T {
    if cond { true_val } else { false_val }
}