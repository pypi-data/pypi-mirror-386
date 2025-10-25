import typing

class Queue():
  def __init__(self) -> None:
    self.que = []

  def pop(self):
    raise NotImplementedError("This method should be overridden by subclasses")

  def push(self, value):
    raise NotImplementedError("This method should be overridden by subclasses")

  def remove(self, value):
    self.que.remove(value)

  def __len__(self):
    return len(self.que)

  def __iter__(self):
      while len(self.que) > 0:
          yield self.pop()


class FIFOQueue[V](Queue):
  def push(self, value : V):
    self.que.append(value)

  def pop(self) -> V:
    return self.que.pop(0)

class PriorityQueueNode[V]:
    def __init__(self, value : V, priority : float):
        self.value : V = value
        self.priority = priority

class PriorityQueue[V](Queue):
  def __init__(self, evaluation_func : typing.Callable[[V], float]):
    super().__init__()
    self.que : list[PriorityQueueNode] = []
    self.evaluation_func = evaluation_func # Returns an evaluation score of a value

  def push(self, value : V) -> None:
    new_node = PriorityQueueNode(value, self.evaluation_func(value))
    for index, que_node in enumerate(self.que):
      if new_node.priority < que_node.priority:
        self.que.insert(index,new_node)
        return

    self.que.append(new_node)

  def pop(self) -> V:
    return self.que.pop(0).value

  def best_eval_peak(self, compared_to : float) -> float:
    for p_node in self.que:
      if p_node.priority >= compared_to:
        return p_node.priority
    return compared_to

  def best(self):
    """Return all items tied for the best (lowest) score."""
    if not self.que:
        return []

    best_score = self.que[0].priority
    out = []
    for q in self.que:
        if q.priority == best_score:
            out.append(q.value)
        else:
            break
    return out

class BoundedPriorityQueue(PriorityQueue):
    def __init__(self, evaluation_func, limit : int):
        assert limit > 0, "Limit must be positive"
        super().__init__(evaluation_func)

        self.limit = limit

    def push(self, value):
        super().push(value)

        if len(self.que) > self.limit:
            self.que = self.que[:self.limit]

class LIFOQueue(Queue):
  def push(self, value):
    self.que.append(value)

  def pop(self):
    return self.que.pop()

# Alias
Stack = LIFOQueue

__all__ = ['Stack', 'FIFOQueue', 'PriorityQueue', 'BoundedPriorityQueue', 'LIFOQueue']