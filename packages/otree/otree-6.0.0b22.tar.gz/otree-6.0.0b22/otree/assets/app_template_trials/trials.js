class Cycle extends BaseCycle {
    onInput(name, value) {
        ot.submitTrialResponse({choice: value});
    }
}