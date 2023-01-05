import os
import pickle


def retrieve(cmd, args, capturer):
  cache_file = os.path.join(args.output_directory, "dljc.cache")

  if args.cache and os.path.exists(cache_file):
    with open(cache_file, 'rb') as f:
      return pickle.load(f)

  result = capturer.gen_instance(cmd, args).capture()

  if not result:
    return None

  javac_commands, jars, stats = result
  with open(cache_file, 'wb') as f:
    pickle.dump((javac_commands, jars, stats), f)

  return javac_commands, jars, stats
