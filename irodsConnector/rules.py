""" rule operations
"""
import logging
import irods.exception
import irods.rule
from irodsConnector.session import Session


class Rules(object):
    """Irods Rule operations """
    _ses_man = None

    def __init__(self, ses_man: Session):
        """ iRODS data operations initialization

            Parameters
            ----------
            ses_man : irods session
                instance of the Session class

        """
        self._ses_man = ses_man

    def execute_rule(self, params: dict, rule_file: str = None, body: str = '', rule_type: str = 'irods_rule_language',
                     output: str = 'ruleExecOut') -> tuple:
        """Execute an iRODS rule.

        Parameters
        ----------
        rule_file : str, file-like
            Name of the iRODS rule file, or a file-like object representing it.
        body    : str,rulename
            Name of the rule on the irods server.
        params : dict
            Rule arguments.
        rule_type : str
            changes between irods rule language and python rules.
        output : str
            Rule output variable(s).

        Returns
        -------
        tuple
            (stdout, stderr)

        `params` format example:
        params = {  # extra quotes for string literals
            '*obj': '"/zone/home/user"',
            '*name': '"attr_name"',
            '*value': '"attr_value"'
        }

        """
        try:
            rule = irods.rule.Rule(
                self._ses_man.session, rule_file=rule_file, body=body, params=params, output=output,
                instance_name=f'irods_rule_engine_plugin-{rule_type}-instance')
            out = rule.execute()
        except irods.exception.NetworkException as netexc:
            logging.info('Lost connection to iRODS server.')
            return '', repr(netexc)
        except irods.exception.SYS_HEADER_READ_LEN_ERR as shrle:
            logging.info('iRODS server hiccuped.  Check the results and try again.')
            return '', repr(shrle)
        except Exception as error:
            logging.info('RULE EXECUTION ERROR', exc_info=True)
            return '', repr(error)
        stdout, stderr = '', ''
        if len(out.MsParam_PI) > 0:
            buffers = out.MsParam_PI[0].inOutStruct
            stdout = (buffers.stdoutBuf.buf or b'').decode()
            # Remove garbage after terminal newline.
            stdout = '\n'.join(stdout.split('\n')[:-1])
            stderr = (buffers.stderrBuf.buf or b'').decode()
        return stdout, stderr
