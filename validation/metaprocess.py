import json
import jsonschema
# from jsonschema.validators import create, _validators, _types
# with open("/run/user/1000/gvfs/sftp:host=5.196.74.56,user=hblanco/var/www/html/schemas/m.json") as f:
#     meta_schema = json.load(f)
# 
# MyValidator = create(
#     meta_schema=meta_schema,
#     validators={
#         u"$ref": _validators.ref,
#         u"additionalItems": _validators.additionalItems,
#         u"additionalProperties": _validators.additionalProperties,
#         u"allOf": _validators.allOf,
#         u"anyOf": _validators.anyOf,
#         u"const": _validators.const,
#         u"contains": _validators.contains,
#         u"dependencies": _validators.dependencies,
#         u"enum": _validators.enum,
#         u"exclusiveMaximum": _validators.exclusiveMaximum,
#         u"exclusiveMinimum": _validators.exclusiveMinimum,
#         u"format": _validators.format,
#         u"if": _validators.if_,
#         u"items": _validators.items,
#         u"maxItems": _validators.maxItems,
#         u"maxLength": _validators.maxLength,
#         u"maxProperties": _validators.maxProperties,
#         u"maximum": _validators.maximum,
#         u"minItems": _validators.minItems,
#         u"minLength": _validators.minLength,
#         u"minProperties": _validators.minProperties,
#         u"minimum": _validators.minimum,
#         u"multipleOf": _validators.multipleOf,
#         u"oneOf": _validators.oneOf,
#         u"not": _validators.not_,
#         u"pattern": _validators.pattern,
#         u"patternProperties": _validators.patternProperties,
#         u"properties": _validators.properties,
#         u"propertyNames": _validators.propertyNames,
#         u"required": _validators.required,
#         u"type": _validators.type,
#         u"uniqueItems": _validators.uniqueItems,
#     },
#     type_checker=_types.draft7_type_checker,
#     version="01",
# )
# 
# # print(MyValidator.ID_OF(MyValidator.META_SCHEMA))
# # print(MyValidator.META_SCHEMA)
# 
# with open("./processIng.json") as f:
#     dataAddIng = json.load(f)
# 
# with open("/home/hblanco/workspace/cookba/cookbase/resources/schemas/process/addingIngredients.json") as f:
#     schemaAddIng = json.load(f)
# 
# with open("./schema.json") as f:
#     schema = json.load(f)
# 
# # jsonschema.validate(meta_schema, {"$schema": "http://www.landarltracker.com/schemas/m.json"}, MyValidator)
# jsonschema.validate(dataAddIng, schemaAddIng, MyValidator)
# # jsonschema.validate({"process": "AAA"}, schema)
# # jsonschema.validate(meta_schema, {"$schema": "http://www.landarltracker.com/schemas/meta-process.json"},cls=MyValidator)
# # jsonschema.validate(data, schema,cls=MyValidator)

with open("/run/user/1000/gvfs/sftp:host=5.196.74.56,user=hblanco/var/www/html/schemas/process/dividing.json") as f:
    schema = json.load(f)
    
from os import listdir
from os.path import isfile, join
path = "/run/user/1000/gvfs/sftp:host=5.196.74.56,user=hblanco/var/www/html/schemas/"
onlyfiles = [f for f in listdir(path + "process/") if isfile(join(path + "process/", f))]
    
for i in onlyfiles:
    with open(path + "process/" + i) as f:
        data = json.load(f)
   
        print(i)

# with open("./processIng.json") as f:
#     data = json.load(f)
    jsonschema.validate(schema, {"$schema": "http://json-schema.org/draft-07/schema#"})
        
        
# with open("/home/hblanco/workspace/cookba/cookbase/resources/schemas/process/separating.json") as f:
#     data = json.load(f)
# jsonschema.validate(data, schema)
    
    
