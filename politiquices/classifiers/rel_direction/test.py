from relationship_direction_clf import DirectionClassifier


def main():
    clf = DirectionClassifier()
    result = clf.detect_direction("Marcelo está completamente louco, diz Sócrates", "Marcelo", "Sócrates")


if __name__ == '__main__':
    main()
