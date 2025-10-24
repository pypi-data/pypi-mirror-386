from .xparser import parse_title

def main():
    import sys
    if len(sys.argv) > 1:
        input_title = " ".join(sys.argv[1:])
    else:
        input_title = input("Enter the news title: ")
    try:
        result = parse_title(input_title)
        print(">", result)
    except Exception as e:
        print(f'Cannot parse: `{input_title}` -> {e}')

if __name__ == '__main__':
    main()
