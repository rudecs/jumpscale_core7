from JumpScale import j
import os

def find_models(basepath):
    specs = dict()
    modelpath = os.path.join(basepath, 'models', 'osis')
    if os.path.exists(modelpath):
        for namespace in j.system.fs.listDirsInDir(modelpath, dirNameOnly=True):
            specpath = os.path.join(modelpath, namespace)
            j.core.specparser.parseSpecs(specpath, 'osismodel', namespace)
            modelnames = j.core.specparser.getModelNames('osismodel', namespace)
            models = dict()
            for modelname in modelnames:
                model = j.core.specparser.getModelSpec('osismodel', namespace, modelname)
                models[modelname] = model
            specs[namespace] = models
    return specs
