import os
import argparse
import common

argparser = argparse.ArgumentParser(add_help=False)
infer_group = argparser.add_argument_group('inference tool arguments')

infer_group.add_argument('-s', '--solver', metavar='<solver>',
                        action='store',default='checkers.inference.solver.DebugSolver',
                        help='solver to use on constraints')
infer_group.add_argument('-afud', '--afuOutputDir', metavar='<afud>',
                        action='store',default='afud/',
                        help='Annotation File Utilities output directory')
infer_group.add_argument('-m', '--mode', metavar='<mode>',
                        action='store',default='INFER',
                        help='Modes of operation: TYPECHECK, INFER, ROUNDTRIP,ROUNDTRIP_TYPECHECK')
infer_group.add_argument('-solverArgs', '--solverArgs', metavar='<solverArgs>',
                        action='store',default='backEndType=maxsatbackend.MaxSat',
                        help='arguments for solver')

def run(args, javac_commands, jars):
    # the dist directory if CFI.
    CFI_dist = os.path.join(os.environ['JSR308'], 'checker-framework-inference', 'dist')
    CFI_command = ['java']

    print os.environ

    for jc in javac_commands:
        target_cp = jc['javac_switches']['classpath']

        cp = target_cp + \
             ':' + os.path.join(CFI_dist, 'checker.jar') + \
             ':' + os.path.join(CFI_dist, 'plume.jar') + \
             ':' + os.path.join(CFI_dist, 'checker-framework-inference.jar')

        cmd = CFI_command + ['-classpath', cp,
                             'checkers.inference.InferenceLauncher',
                             '--solverArgs', args.solverArgs,
                             '--checker', args.checker,
                             '--solver', args.solver,
                             '--mode', args.mode,
                             '--hacks=true',
                             '--targetclasspath', target_cp,
                             '-afud', args.afuOutputDir]
        cmd.extend(jc['java_files'])

        common.run_cmd(cmd)
