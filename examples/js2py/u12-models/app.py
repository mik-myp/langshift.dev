from models import Estimate, Plan, Task, UrgentTask


def main() -> None:
    read = Task("Read", 30)
    write = UrgentTask("Write", 15)
    plan = Plan([read, write])
    print(plan.remaining_minutes())
    print(read.mark_done(), read.mark_done())
    print(plan.remaining_minutes())
    print(write.label())
    first = Estimate("Read", 30)
    second = Estimate("Read", 30)
    print(first == second, first is second)
    first.tags.append("python")
    print(first.tags, second.tags)


if __name__ == "__main__":
    main()
