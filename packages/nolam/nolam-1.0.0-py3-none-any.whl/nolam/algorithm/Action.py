from nolam.algorithm.Operator import Operator


class Action(Operator):

    def __init__(self, operator_name, parameters, precs_pos=None,  precs_neg=None, eff_pos=None, eff_neg=None):

        super().__init__(operator_name, parameters, precs_pos, precs_neg, eff_pos, eff_neg)

        self.params_bind = {f'?param_{i + 1}': obj for i, obj in enumerate(parameters)}

    def __str__(self):
        if len(self.parameters) > 0:
            return f"({self.operator_name} {' '.join(self.parameters)})"
        return f"({self.operator_name})"

    # def add_prec_cert(self, precondition):
    #     self.precs_cert.add(precondition)
    #     self.remove_prec_uncert(precondition)
    #
    # def remove_prec_uncert(self, precondition):
    #     if precondition in self.precs_uncert:
    #         self.precs_uncert.remove(precondition)
    #
    # def add_eff_pos_cert(self, effect):
    #     self.eff_pos_cert.add(effect)
    #     self.remove_eff_neg_uncert(effect)
    #     self.remove_eff_pos_uncert(effect)
    #
    # def remove_eff_pos_uncert(self, effect):
    #     if effect in self.eff_pos_uncert:
    #         self.eff_pos_uncert.remove(effect)
    #
    # def add_eff_neg_cert(self, effect):
    #     self.eff_neg_cert.add(effect)
    #     self.remove_eff_neg_uncert(effect)
    #     self.remove_eff_pos_uncert(effect)
    #
    # def remove_eff_neg_uncert(self, effect):
    #     if effect in self.eff_neg_uncert:
    #         self.eff_neg_uncert.remove(effect)
