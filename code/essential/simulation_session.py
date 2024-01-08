from essential.layer import LayerForResult


class SimulationSession :
    def __init__(self, layer_list):
        super().__init__()

        self.layers = layer_list
        self.solutions = []
        self.layers_output = []
        self.get_solution()
        self.get_layer_list()


    def get_solution(self):
        self.solutions = []

        for i, layer in enumerate(self.layers):
            if i > 0 and i < len(self.layers) - 1:
                tickness = (layer.data["thickness"]["low"] + layer.data["thickness"]["high"])/2
                self.solutions.append(tickness)

            if layer.fb_term is not None:
                n_inf = (layer.data["n inf"]["low"] + layer.data["n inf"]["high"])/2
                band_gap = (layer.data["eg"]["low"] + layer.data["eg"]["high"])/2
                self.solutions.append(n_inf)
                self.solutions.append(band_gap)

                for i in range(layer.fb_term):
                    center = (layer.data[f"center_{i}"]["low"] + layer.data[f"center_{i}"]["high"])/2
                    width = (layer.data[f"width_{i}"]["low"] + layer.data[f"width_{i}"]["high"])/2
                    area = (layer.data[f"area_{i}"]["low"] + layer.data[f"area_{i}"]["high"])/2
                    self.solutions.append(center)
                    self.solutions.append(width)
                    self.solutions.append(area)


    def get_layer_list(self):
        self.layers_output = []
        for i, layer in enumerate(self.layers):
            if i ==0 or i==len(self.layers)-1:
                self.layers_output.append(LayerForResult(layer.name,layer.nk_file,layer.fb_term,True))
            else:
                self.layers_output.append(LayerForResult(layer.name,layer.nk_file,layer.fb_term,False))

    def get_result(self):
        return self.layers_output , self.solutions


