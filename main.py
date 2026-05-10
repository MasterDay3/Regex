from __future__ import annotations
from abc import ABC, abstractmethod


class State(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def check_self(self, char: str) -> bool:
        """
        function checks whether occured character is handled by current ctate
        """
        pass

    def check_next(self, next_char: str) -> State | Exception:
        for state in self.next_states:
            if state.check_self(next_char):
                return state
        raise NotImplementedError("rejected string")


class StartState(State):
    next_states: list[State] = []

    def __init__(self):
        super().__init__()

    def check_self(self, char):
        return super().check_self(char)


class TerminationState(State):
    next_states: list[State] = []

    def __init__(self):
        pass

    def check_self(self, char: str) -> bool:
        return False


class DotState(State):
    """
    state for . character (any character accepted)
    """

    next_states: list[State] = []

    def __init__(self):
        super().__init__()

    def check_self(self, char: str) -> bool:
        return len(char) == 1


class AsciiState(State):
    """
    state for alphabet letters or numbers
    """

    next_states: list[State] = []
    curr_sym = ""

    def __init__(self, symbol: str) -> None:
        self.curr_sym = symbol

    def check_self(self, curr_char: str) -> bool:
        if curr_char == self.curr_sym:
            return True
        return False


class StarState(State):
    next_states: list[State] = []

    def __init__(self, checking_state: State):
        self.checking_state = checking_state
        self.next_states = [checking_state]

    def check_self(self, char):
        for state in self.next_states:
            if state.check_self(char):
                return True
        return False


class PlusState(State):
    next_states: list[State] = []

    def __init__(self, checking_state: State):
        self.checking_state = checking_state
        self.next_states = []

    def check_self(self, char) -> bool:
        return self.checking_state.check_self(char)


class RegexFSM:
    curr_state: State = StartState()

    def __init__(self, regex_expr: str) -> None:
        self.curr_state = StartState()
        self.curr_state.next_states = []
        prev_state = self.curr_state
        tmp_next_state = self.curr_state
        for char in regex_expr:
            tmp_next_state = self.__init_next_state(char, prev_state, tmp_next_state)
            prev_state.next_states.append(tmp_next_state)
            prev_state = tmp_next_state
        term = TerminationState()
        prev_state.next_states.append(term)

    def __init_next_state(
        self, next_token: str, prev_state: State, tmp_next_state: State
    ) -> State:
        new_state = None
        match next_token:
            case next_token if next_token == ".":
                new_state = DotState()
                new_state.next_states = []
            case next_token if next_token == "*":
                grandparent = tmp_next_state._prev
                grandparent.next_states.remove(tmp_next_state)
                new_state = StarState(tmp_next_state)
                new_state._prev = grandparent
                grandparent.next_states.append(new_state)
            case next_token if next_token == "+":
                new_state = PlusState(tmp_next_state)
                new_state.next_states = []
                new_state._prev = tmp_next_state
            case next_token if next_token.isascii():
                new_state = AsciiState(next_token)
                new_state.next_states = []
                new_state._prev = prev_state
            case _:
                raise AttributeError("Character is not supported")
        if not hasattr(new_state, "_prev"):
            new_state._prev = prev_state
        return new_state

    def check_string(self, text: str) -> bool:
        def get_epsilon_closure(states):
            closure = []
            for s in states:
                if s not in closure:
                    closure.append(s)
            changed = True
            while changed:
                changed = False
                new_closure = []
                for s in closure:
                    if s not in new_closure:
                        new_closure.append(s)
                for s in closure:
                    for nxt in s.next_states:
                        if isinstance(nxt, StarState) and nxt not in new_closure:
                            new_closure.append(nxt)
                            changed = True
                        if isinstance(nxt, (StarState, PlusState)):
                            for nxt2 in nxt.next_states:
                                if nxt2 not in new_closure:
                                    new_closure.append(nxt2)
                                    changed = True
                        elif (
                            isinstance(nxt, TerminationState) and nxt not in new_closure
                        ):
                            new_closure.append(nxt)
                closure = new_closure
            return closure

        current_states = get_epsilon_closure([self.curr_state])
        for char in text:
            next_states = []
            for state in current_states:
                for candidate in state.next_states:
                    if candidate.check_self(char):
                        already = False
                        for existing in next_states:
                            if existing is candidate:
                                already = True
                                break
                        if not already:
                            next_states.append(candidate)
                if isinstance(state, (StarState, PlusState)):
                    if state.check_self(char):
                        already = False
                        for existing in next_states:
                            if existing is state:
                                already = True
                                break
                        if not already:
                            next_states.append(state)
            if not next_states:
                return False
            current_states = get_epsilon_closure(next_states)
        for state in current_states:
            if isinstance(state, TerminationState):
                return True
            for nxt in state.next_states:
                if isinstance(nxt, TerminationState):
                    return True
        return False


if __name__ == "__main__":
    regex_pattern = "a*4.+hi"
    regex_compiled = RegexFSM(regex_pattern)
    print(regex_compiled.check_string("aaaaaa4uhi"))  # True
    print(regex_compiled.check_string("4uhi"))  # True
    print(regex_compiled.check_string("meow"))  # False
