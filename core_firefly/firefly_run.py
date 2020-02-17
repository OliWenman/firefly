import firefly_class

ff = firefly_class.Firefly()

file_input = "./example_data/CDFS022490.ascii"

ff.model_input()
ff.file_input(file = file_input)
ff.settings()
ff.run()
