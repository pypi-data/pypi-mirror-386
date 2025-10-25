#ifndef AMPL_AMPL_C_H
#define AMPL_AMPL_C_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>

#include "ampl/nanoarrow.h"

#include "ampl/arg_c.h"
#include "ampl/dataframe_c.h"
#include "ampl/declaration_c.h"
#include "ampl/environment_c.h"
#include "ampl/errorhandler_c.h"
#include "ampl/nanoarrow.h"
#include "ampl/output_c.h"
#include "ampl/tuple_c.h"
#include "ampl/variant_c.h"


typedef void (*RunnablePtr)(void* runnable);

AMPLAPI int AMPL_StringFree(char **string);

AMPLAPI void AMPL_AddToPath(const char *newPath);

/**
 * \defgroup AMPL AMPL struct functions
 * @{
 * An %AMPL translator.
 *
 * An %AMPL struct can be used to do the following tasks:
 *
 * <ul>
 * <li>Run %AMPL code. See AMPL_Eval().
 * <li>Read models and data from files. See AMPL_Read() and AMPL_ReadData().
 * <li>Solve optimization problems constructed from model and data (see
 * AMPL_Solve()).
 * <li>Access lists of available entities of an optimization problem. See
 * AMPL_GetVariables(), AMPL_GetObjectives(), AMPL_GetConstraints(),
 * AMPL_GetSets() and AMPL_GetParameters().
 * </ul>
 *
 * %AMPL stores one or more problems which may consume substantial amount of
 * memory. The %AMPL struct has a deallocator which automaticallly closes the
 * underlying %AMPL interpreter.
 * <p>
 * Consistency is *not* maintained automatically. Any command issued to the
 * translator through eval and similar functions do *not* invalidate all
 * entities, and any further access to any entity will require a new call to the
 * entity. <p> Error handling is two-faced: <ul> <li>Errors coming from the
 * underlying %AMPL translator (e.g. syntax errors and warnings obtained calling
 * the eval method) are handled by the ErrorHandler which can be set and get via
 * AMPL_GetErrorHandler() and AMPL_SetErrorHandler(). <li>Generic errors coming
 * from misusing the API, which are detected in C, are returned by any function
 * as the AMPL_ERRORINFO struct.
 * </ul>
 * TODO
 * The default implementation of the error handler throws exceptions on errors
 * and prints to console on warnings.
 * <p>
 * The output of every user interaction with the underlying translator is
 * handled implementing the abstract class ampl::OutputHandler. The (only)
 * method is called at each block of output from the translator. The current
 * output handler can be accessed and set via AMPL::getOutputHandler()
 * and AMPL::setOutputHandler().
 * TODO
 */

/**
 * An AMPL translator.
 */
typedef struct Ampl AMPL;

/**
 * Allocates the AMPL struct with the default environment.
 *
 * \param ampl Pointer to the pointer of the AMPL struct.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_Create(AMPL **ampl);

/**
 * Allocates the AMPL struct with the specified environment.
 * This allows the user to specify the location of the AMPL binaries to be used
 * and to modify the environment variables in which the AMPL interpreter will
 * run.
 *
 * \param ampl Pointer to the pointer of the AMPL struct.
 * \param env Pointer to the AMPL environment struct.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_CreateWithEnv(AMPL **ampl, AMPL_ENVIRONMENT *env);

/**
 * Frees the AMPL struct.
 *
 * \param ampl Pointer to the pointer of the AMPL struct.
 */
AMPLAPI void AMPL_Free(AMPL **ampl);

/**
 * Parses %AMPL code and evaluates it as a possibly empty sequence of %AMPL
 * declarations and statements.
 * <p>
 * As a side effect, it invalidates all entities (as the passed statements
 * can contain any arbitrary command); the lists of entities will be
 * re-populated lazily (at first access)
 * <p>
 * The output of interpreting the statements is passed to the current
 * OutputHandler (see getOutputHandler and
 * setOutputHandler).
 * <p>
 * By default, errors are reported as exceptions and warnings are printed on
 * stdout. This behavior can be changed reassigning an
 * ErrorHandler using setErrorHandler.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param statement
 *            A collection of %AMPL statements and declarations to be
 *            passed to the interpreter.
 * \return Pointer to the AMPL error info struct.
 *
 * @throws std::runtime_error
 *             if the input is not a complete %AMPL statement (e.g.
 *             if it does not end with semicolon) or if the underlying
 *             interpreter is not running
 */
AMPLAPI AMPL_ERRORINFO *AMPL_Eval(AMPL *ampl, const char *statement);

/** 
 * Interpret the given %AMPL statement asynchronously.
 * 
 * \param ampl Pointer to the AMPL struct.
 * \param statement A collection of %AMPL statements and declarations to be
 *            passed to the interpreter.
 * \param function TODO
 * \param cb TODO
 * \return Pointer to the AMPL error info struct.
 * 
 * Throws runtime_error if the underlying ampl interpreter is not running
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EvalAsync(AMPL *ampl, const char *statement,
                               RunnablePtr function, void *cb);

/**
 * Solve the current model asynchronously.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param function TODO
 * \param cb TODO
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SolveAsync(AMPL *ampl, RunnablePtr function,
                                void *cb);

/**
 * Interprets the specified file asynchronously, interpreting it as a model
 * or a script file. As a side effect, it invalidates all entities (as the
 * passed file can contain any arbitrary command); the lists of entities
 * will be re-populated lazily (at first access).
 *
 * \param ampl Pointer to the AMPL struct.
 * \param filename Path to the file (Relative to the current working directory or
 *                 absolute).
 * \param function TODO
 * \param cb TODO
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ReadAsync(AMPL *ampl, const char *filename, RunnablePtr function,
                                    void *cb);

/**
 * Interprets the specified data file asynchronously. When interpreting is
 * over, the specified callback is called. The file is interpreted as data.
 * As a side effect, it invalidates all entities (as the passed file can
 * contain any arbitrary command); the lists of entities will be
 * re-populated lazily (at first access).
 *
 * \param ampl Pointer to the AMPL struct.
 * \param filename Full path to the file.
 * \param function TODO
 * \param cb TODO
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ReadDataAsync(AMPL *ampl, const char *filename, RunnablePtr function,
                                    void *cb);

/**
 * Clears all entities in the underlying %AMPL interpreter, clears all maps
 * and invalidates all entities.
 *
 * \param ampl Pointer to the AMPL struct.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_Reset(AMPL *ampl);

/**
 * Clears all data..
 *
 * \param ampl Pointer to the AMPL struct.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ResetData(AMPL *ampl);

/**
 * Stops the underlying engine, and release all any further attempt to execute
 * optimisation commands without restarting it will throw an exception.
 *
 * \param ampl Pointer to the AMPL struct.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_Close(AMPL *ampl);

/**
 * Returns true if the underlying engine is running.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param running TODO
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_IsRunning(AMPL *ampl, bool *running);

/**
 * Returns true if the underlying engine is doing an async operation.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param busy TODO
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_IsBusy(AMPL *ampl, bool *busy);

/**
 * Solve the current model.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param problem Name of the problem to solve as a string.
 * \param solver Name of the solver to use as a string.
 * \return Pointer to the AMPL error info struct.
 *
 * \throws std::runtime_error If the underlying interpreter is not running
 */
AMPLAPI AMPL_ERRORINFO *AMPL_Solve(AMPL *ampl, const char *problem,
                                   const char *solver);

/**
 * Interrupts the underlying engine.
 *
 * \param ampl Pointer to the AMPL struct.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_Interrupt(AMPL *ampl);

/**
 * Take a snapshot of the AMPL session.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param fileName The file where to write the snapshot to.
 * \param model Include model if set to not 0.
 * \param data Include data if set to not 0.
 * \param options Include options if set to not 0.
 * \param output TODO
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_Snapshot(AMPL *ampl, const char *fileName,
                                      bool model, bool data, bool options,
                                      char **output);

/**
 * Write the declarations that were made in the current AMPL struct
 * to a file.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param fileName The file where to write the declarations to.
 * \param output TODO
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ExportModel(AMPL *ampl, const char *fileName,
                                         char **output);

/**
 * Write all data loaded in the current instance to a file.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param fileName The file where to write the data to.
 * \param output TODO
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ExportData(AMPL *ampl, const char *fileName,
                                        char **output);

/**
 * Get the current working directory from the underlying interpreter (see
 * https://en.wikipedia.org/wiki/Working_directory).
 *
 * \param ampl Pointer to the AMPL struct.
 * \param output Current working directory.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_Cd(AMPL *ampl, char **output);

/**
 * Change or display the current working directory (see
 * https://en.wikipedia.org/wiki/Working_directory ).
 *
 * \param ampl Pointer to the AMPL struct.
 * \param path New working directory or null (to display the working
 *             directory).
 * \param output Current working directory.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_Cd2(AMPL *ampl, const char *path, char **output);

/**
 * Get the name of the currently active objective (see the ``objective``
 * command)
 *
 * \param ampl Pointer to the AMPL struct.
 * \param currentObjective Current objective or empty string if no objective has
 * been declared. \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetCurrentObjective(AMPL *ampl,
                                                 char **currentObjective);

/**
 * Set an %AMPL option to a specified value.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param name Name of the option to be set (alphanumeric without spaces).
 * \param value String representing the value the option must be set to.
 * \return Pointer to the AMPL error info struct.
 * @throws std::invalid_argument
 *             if the option name is not valid
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetOption(AMPL *ampl, const char *name,
                                       const char *value);

/**
 * Get the current value of the specified option. If the option does not
 * exist, the parameter exists will be set to false.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param name Option name (alphanumeric)
 * \param exists True if the option exists, false otherwise.
 * \param value Pointer to the value of the option as a string.
 * \return Pointer to the AMPL error info struct.
 * @throws std::invalid_argument if the option name is not valid
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetOption(AMPL *ampl, const char *name,
                                       bool *exists, char **value);

/**
 * Get the current value of the specified integer option.
 * If the option does not exist, the parameter exists will be set to false.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param name Option name (alphanumeric).
 * \param exists True if the option exists, false otherwise.
 * \param value Pointer to the value of the option as an integer.
 * \return Pointer to the AMPL error info struct.
 * @throws std::invalid_argument
 *             if the option name is not valid
 * @throws std::invalid_argument
 *             If the option did not have a value which could be casted to
 *             integer
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetIntOption(AMPL *ampl, const char *name,
                                          bool *exists, int *value);

/**
 * Get the current value of the specified double option.
 * If the option does not exist, the parameter exists will be set to false.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param name Option name (alphanumeric).
 * \param exists True if the option exists, false otherwise.
 * \param value Pointer to the value of the option as an double.
 * \return Pointer to the AMPL error info struct.
 * @throws std::invalid_argument
 *             if the option name is not valid
 * @throws std::invalid_argument
 *             If the option did not have a value which could be casted to
 *             double
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetDblOption(AMPL *ampl, const char *name,
                                          bool *exists, double *value);

/**
 * Set an %AMPL double option to a specified value.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param name Name of the double option to be set (alphanumeric without
 * spaces).
 * \param value Double representing the value the option must be set
 * to.
 * \return Pointer to the AMPL error info struct.
 * @throws std::invalid_argument
 *             if the option name is not valid
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetDblOption(AMPL *ampl, const char *name,
                                          double value);

/**
 * Set an %AMPL integer option to a specified value.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param name Name of the double option to be set (alphanumeric without
 * spaces).
 * \param value Integer representing the value the option must be set
 * to.
 * \return Pointer to the AMPL error info struct.
 * @throws std::invalid_argument
 *             if the option name is not valid
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetIntOption(AMPL *ampl, const char *name,
                                          int value);

/**
 * Get the current value of the specified boolean option.
 * If the option does not exist, the parameter exists will be set to false.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param name Option name (alphanumeric).
 * \param exists True if the option exists, false otherwise.
 * \param value Pointer to the value of the option as a boolean.
 * \return Pointer to the AMPL error info struct.
 * @throws std::invalid_argument
 *             if the option name is not valid
 * @throws std::invalid_argument
 *             If the option did not have a value which could be casted to
 *             boolean
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetBoolOption(AMPL *ampl, const char *name, bool *exists,
                                  bool *value);

/**
 * Set an %AMPL boolean option to a specified value.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param name Name of the boolean option to be set (alphanumeric without
 * spaces).
 * \param value Boolean representing the value the option must be set
 * to.
 * \return Pointer to the AMPL error info struct.
 * @throws std::invalid_argument
 *             if the option name is not valid
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetBoolOption(AMPL *ampl, const char *name, bool value);

/**
 * Interprets the specified file (script or model or mixed). TODO: how to handle
 * updated entities now? \param ampl Pointer to the AMPL struct. \param fileName
 * Full path to the file. \return Pointer to the AMPL error info struct.
 *
 * \throws	runtime_error	In case the file does not exist.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_Read(AMPL *ampl, const char *fileName);

/**
 * Interprets the specified file as an %AMPL data file. As a side effect, it
 * invalidates all entities (as the passed file can contain any arbitrary
 * command); the lists of entities will be re-populated lazily (at first
 * access). After reading the file, the interpreter is put back to "model" mode.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param	fileName	Full path to the file.
 * \return Pointer to the AMPL error info struct.
 * \throws	std::runtime_error	In case the file does not exist.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ReadData(AMPL *ampl, const char *fileName);

/**
 * Get the data corresponding to the display statements. The statements can
 * be %AMPL expressions, or entities. It captures the equivalent of the
 * command:
 *
  \rst
  .. code-block:: ampl

    display ds1, ..., dsn;

  \endrst

  where ``ds1, ..., dsn`` are the ``displayStatements`` with which the
  function is called.

 * As only one DataFrame is returned, the operation will fail if the results
 * of the display statements cannot be indexed over the same set. As a
 * result, any attempt to get data from more than one set, or to get data
 * for multiple parameters with a different number of indexing sets will
 * fail.
 *
 * \param ampl Pointer to the AMPL struct.
 * \param displayStatements The display statements to be fetched.
 * \param n Number of displayStatements.
 * \param output DataFrame capturing the output of the display command in
 tabular form.
 * \return Pointer to the AMPL error info struct.
 *  @throws AMPLException
 *            if the %AMPL visualization command does not succeed for one of
 *            the reasons listed above.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetData(AMPL *ampl,
                                     const char *const *displayStatements,
                                     size_t n, AMPL_DATAFRAME **output);

AMPLAPI AMPL_ERRORINFO *AMPL_GetDataArrow(AMPL *ampl, const char *const *displayStatements,
                                          size_t n, struct AMPL_DataFrameArrow **dataframe_arrow);

/**
 * Assign the data in the dataframe to the %AMPL entities with the names
 * corresponding to the column names. If setName is null, only the
 * parameters value will be assigned.
 *
 * \param	ampl	Pointer to the AMPL struct.
 * \param	df The dataframe containing the data to be assigned.
 * \param	setName	The name of the set to which the indices values
 * of the DataFrame are to be assigned.
 * \return Pointer to the AMPL error info struct.
 *
 * @throws	AMPLException	If the data
 * assignment procedure was not successful.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetData(AMPL *ampl, AMPL_DATAFRAME *df,
                                           const char *setName);

AMPLAPI AMPL_ERRORINFO *AMPL_SetDataArrow(AMPL *ampl, AMPL_DATAFRAMEARROW *df,
                                   const char *setName);

/**
 * Get a string describing the object. Returns the version of the API and
 * either the version of the interpreter or the message "AMPL is not
 * running" if the interpreter is not running (e.g. due to unexpected
 * internal error or to a call AMPL_Close).
 *
 * \param ampl Pointer to the AMPL struct.
 * \param output Pointer to the value of the option as a string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ToString(AMPL *ampl, char **output);

/**
 * Read the table corresponding to the specified name, equivalent to the
 * %AMPL statement:
 *
  \rst
  .. code-block:: ampl

    read table tableName;

  \endrst
 *
 * \param	ampl	Pointer to the AMPL struct.
 * \param	tableName	Name of the table to be read.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ReadTable(AMPL *ampl, const char *tableName);

/**
 * Write the table corresponding to the specified name, equivalent to the
 * %AMPL statement:
 *
  \rst
  .. code-block:: ampl

    write table tableName;

  \endrst
 *
 * \param	ampl	Pointer to the AMPL struct.
 * \param	tableName	 Name of the table to be written.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_WriteTable(AMPL *ampl, const char *tableName);

/**
 * Write model instances. Equivalent to
 *
   \rst
   .. code-block:: ampl

    option auxfiles auxfiles;
    write filename;

   \endrst
 *
 * \param	ampl	Pointer to the AMPL struct.
 * \param	filename	The name of the file to write; the first letter
 * indicates which filetype to write (see the output of ``ampl -o?``).
 * \param auxfiles   The auxiliary files to write. Most notably, 'cr' instructs
 * %AMPL to write out column and row names respectively.
 * \return Pointer to the AMPL error info struct.
 *
 * \throws	PresolveException if the model is not exported because of the
 presolver (most notably if the model is
 * trivial).
 * \throws  InfeasibilityException if the model is not exported because
 * detected infeasible by the presolver.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_Write(AMPL *ampl, const char *filename,
                                   const char *auxfiles);

/**
 * Get a scalar value from the underlying %AMPL interpreter, as a double or a
 * string. \param	ampl	Pointer to the AMPL struct. \param
 * scalarExpression	An %AMPL expression which evaluates to a scalar value.
 * \param	v	Pointer to the value of the expression.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetValue(AMPL *ampl, const char *scalarExpression,
                                      AMPL_VARIANT **v);

/**
 * Get a scalar value from the underlying %AMPL interpreter, as a string.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	scalarExpression An %AMPL expression which evaluates to a scalar
 * value.
 * \param	value	Pointer to the value of the expression.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetValueString(AMPL *ampl, const char *scalarExpression,
                                     char **value);

/**
 * Get a scalar value from the underlying %AMPL interpreter, as a double.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	scalarExpression An %AMPL expression which evaluates to a scalar
 * value.
 * \param	value	Pointer to the value of the expression.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetValueNumeric(AMPL *ampl,
                                             const char *scalarExpression,
                                             double *value);

/**
 * Equivalent to AMPL_Eval() but returns the output as a string.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	amplstatement An %AMPL statement to be evaluated.
 * \param	output Pointer to the value of the option as a string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetOutput(AMPL *ampl, const char *amplstatement,
                                       char **output);


AMPLAPI AMPL_ERRORINFO *AMPL_CallVisualisationCommandOnNames(
    AMPL *ampl, const char *command, const char *const *args, size_t nargs);
AMPLAPI AMPL_ERRORINFO *AMPL_SetOutputHandler(AMPL *ampl, 
                                              AMPL_OutputHandlerCb callback, void *usrdata);
AMPLAPI AMPL_ERRORINFO *AMPL_SetErrorHandler(AMPL *ampl,
                                             ErrorHandlerCbPtr callback, void *usrdata);
AMPLAPI AMPL_ERRORINFO *AMPL_GetOutputHandler(AMPL *ampl, void **usrdata);
AMPLAPI AMPL_ERRORINFO *AMPL_GetErrorHandler(AMPL *ampl, void **usrdata);

/**
 * Get all the variables declared.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	size Pointer to the number of variables.
 * \param	names Pointer to the array of strings representing all declared
 *              variables.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetVariables(AMPL *ampl, size_t *size,
                                          char ***names);

/**
 * Get all the constraints declared.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	size Pointer to the number of constraints.
 * \param	names Pointer to the array of strings representing all declared
 *              constraints.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetConstraints(AMPL *ampl, size_t *size,
                                            char ***names);

/**
 * Get all the parameters declared.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	size Pointer to the number of parameters.
 * \param	names Pointer to the array of strings representing all declared
 *              parameters.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetParameters(AMPL *ampl, size_t *size,
                                           char ***names);

/**
 * Get all the objectives declared.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	size Pointer to the number of objectives.
 * \param	names Pointer to the array of strings representing all declared
 *              objectives.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetObjectives(AMPL *ampl, size_t *size,
                                           char ***names);

/**
 * Get all the sets declared.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	size Pointer to the number of sets.
 * \param	names Pointer to the array of strings representing all declared
 *              sets.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetSets(AMPL *ampl, size_t *size, char ***names);

/**
 * Get all the problems declared.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	size Pointer to the number of problems.
 * \param	names Pointer to the array of strings representing all declared
 *              problems.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_GetProblems(AMPL *ampl, size_t *size,
                                         char ***names);

/**@}*/

AMPLAPI AMPL_ERRORINFO *AMPL_DataFrameCreate3(AMPL_DATAFRAME **dataframe, AMPL *ampl,
                                  const char *const *args, size_t nargs);

/**
 * \defgroup AMPL_ENTITY AMPL Entity functions
 * @{
 *
 */

typedef enum {
  AMPL_VARIABLE,
  AMPL_CONSTRAINT,
  AMPL_OBJECTIVE,
  AMPL_PARAMETER,
  AMPL_SET,
  AMPL_TABLE,
  AMPL_PROBLEM,
  AMPL_UNDEFINED
} AMPL_ENTITYTYPE;

/**
 * Get the indexarity of this entity (sum of the dimensions of the indexing
 * sets).
 * This value indicates the arity of the Tuple to be passed to the method
 * BasicEntity::get() in order to access an instance of this entity.
 * See the following %AMPL examples
 * \rststar
 *
 * .. code-block:: ampl
 *
 *       var x;               # indexarity = 0
 *       var y {1..2};        # indexarity = 1
 *       var z {1..2,3..4};   # indexarity = 2
 *       var zz {{(1, 2)}};   # indexarity = 2
 *
 * \endrststar
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of entity as string.
 * \param arity Pointer to the sum of the dimensions of the indexing sets 
 *              or 0 if the entity is not indexed.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EntityGetIndexarity(AMPL *ampl, const char *name,
                                                 size_t *arity);

/**
 * Get the names of all entities which depend on this one.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of entity as string.
 * \param	xref Pointer to the array of strings representing all entities.
 * \param	size Pointer to the number of entities which depend on this one.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EntityGetXref(AMPL *ampl, const char *name,
                                           char ***xref, size_t *size);

/**
 * Get the number of instances of this entity.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of entity as string.
 * \param	size Pointer to the number of instances of this entity.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EntityGetNumInstances(AMPL *ampl, const char *name,
                                                   size_t *size);

/**
 * Get all indices as tuples of this entity.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of entity as string.
 * \param	tuples Pointer to the array of tuples representing all indicies of this entity.
 * \param	size Pointer to the number of indices of this entity.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EntityGetTuples(AMPL *ampl, const char *name,
                                             AMPL_TUPLE ***tuples,
                                             size_t *size);

/**
 * Get the %AMPL string representation of the sets on which this entity is
 * indexed (an empty array if the entity is scalar).
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of entity as string.
 * \param	indexingsets Pointer to the array of strings representing the indexing sets.
 * \param	size Pointer to the number of indexing sets.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EntityGetIndexingSets(AMPL *ampl, const char *name,
                                                   char ***indexingsets,
                                                   size_t *size);

/**
 * Get the type of this entity.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of entity as string.
 * \param	type Pointer to the type of the entity.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EntityGetType(AMPL *ampl, const char *name,
                                           AMPL_ENTITYTYPE *type);
        
/**
 * Get the type of this entity as string.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of entity as string.
 * \param	typestr Pointer to the type of the entity as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EntityGetTypeString(AMPL *ampl, const char *name,
                                                 const char **typestr);

/**
 * Get the declaration of this entity as string.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of entity as string.
 * \param	declaration Pointer to the declaration of the entity as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EntityGetDeclaration(AMPL *ampl, const char *name,
                                                  char **declaration);

/**
 * Drop all instances in this entity, corresponding to the %AMPL
 * code: `drop name;`
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of entity as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EntityDrop(AMPL *ampl, const char *name);

/**
 * Restore all instances in this entity, corresponding to the %AMPL
 * code: `restore name;`
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of entity as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EntityRestore(AMPL *ampl, const char *name);

/**
 * Get the values of this entity.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of entity as string.
 * \param	suffixes Suffixes to get the values of.
 * \param	n Number of suffixes.
 * \param	output Pointer to the dataframe containing the values of the entity.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EntityGetValues(AMPL *ampl, const char *name,
                                             const char *const *suffixes,
                                             size_t n, AMPL_DATAFRAME **output);

AMPLAPI AMPL_ERRORINFO *AMPL_EntityGetValuesArrow(AMPL *ampl, const char *name,
                                                  const char *const *suffixes, size_t n,
                                                  struct ArrowSchema **schema, struct ArrowArray **array);

/**
 * Set the values of this entity.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of entity as string.
 * \param	data Pointer to the dataframe containing the values of the entity to be set.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_EntitySetValues(AMPL *ampl, const char *name,
                                             AMPL_DATAFRAME *data);

AMPLAPI AMPL_ERRORINFO *AMPL_EntitySetValuesArrow(AMPL *ampl, const char *name,
                                                  AMPL_DATAFRAMEARROW *dataframe);

AMPLAPI AMPL_ERRORINFO *AMPL_EntitySetSuffixes(AMPL *ampl, const char *name,
  AMPL_DATAFRAME *data);

AMPLAPI AMPL_ERRORINFO *AMPL_EntitySetSuffixesArrow(AMPL *ampl, const char *name,
                                                    AMPL_DATAFRAMEARROW *dataframe);

/**@}*/


/**
 * \defgroup AMPL_PARAMETER AMPL Parameter functions
 * @{
 * 
 * Represents an AMPL parameter.
 * The values are AMPL_VARIANTs.
 * Data can be assigned to the parameter using the functions AMPL_ParameterSetValue() and AMPL_ParameterSetArgsValues() or using AMPL_SetData() and a AMPL_DATAFRAME struct. 
 *
 */

/**
 * Set the value of a scalar parameter.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	scalarExpression Name of scalar parameter as string.
 * \param	v Pointer to variant to set the value of a scalar parameter to.
 * \return Pointer to the AMPL error info struct.
 * 
 *   @throws runtime_error
              if the entity has been deleted in the underlying %AMPL
     @throws logic_error
              if this parameter is not scalar.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterSetValue(AMPL *ampl,
                                               const char *scalarExpression,
                                               AMPL_VARIANT *v);

/**
 * Set the value of a scalar parameter to numeric value.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	scalarExpression Name of scalar parameter as string.
 * \param	value Double value to set the value of a scalar parameter to.
 * \return Pointer to the AMPL error info struct.
 * 
 *   @throws runtime_error
              if the entity has been deleted in the underlying %AMPL
     @throws logic_error
              if this parameter is not scalar.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterSetNumeric(AMPL *ampl,
                                                 const char *scalarExpression,
                                                 double value);

/**
 * Set the value of a scalar parameter to string value.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	scalarExpression Name of scalar parameter as string.
 * \param	value String value to set the value of a scalar parameter to.
 * \return Pointer to the AMPL error info struct.
 * 
 *   @throws runtime_error
              if the entity has been deleted in the underlying %AMPL
     @throws logic_error
              if this parameter is not scalar.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterSetString(AMPL *ampl,
                                                const char *scalarExpression,
                                                const char *value);

/**
 * Returns true if the parameter is declared as symbolic
 * (can store both numerical and string values).
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of parameter as string.
 * \param	isSymbolic True if the parameter is symbolic, false otherwise (pointer to bool).
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterIsSymbolic(AMPL *ampl, const char *name,
                                                 bool *isSymbolic);

  /**
  \rst
  Check if the parameter has a default initial value. In case of the following
  AMPL code:

  .. code-block:: ampl

    param a;
    param b default a;

  the function will return true for parameter ``b``.
  \endrst

  * \param ampl Pointer to the AMPL struct.
  * \param name Name of parameter as string.
  * \param hasDefault True if the parameter has a default initial value. Please note
  *                  that if the parameter has a default expression which refers to
  *                  another parameter which value is not defined, this will return true.
  * \return Pointer to the AMPL error info struct.
  */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterHasDefault(AMPL *ampl, const char *name,
                                                 bool *hasDefault);

/**
 * Assign the specified size double values to this parameter, assigning them to
 * the parameter in the same order as the indices in the entity.
 * The number of values in the array must be equal to the
 * specified size.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of parameter as string.
 * \param	size Number of values to be assigned.
 * \param	args Values to be assigned as doubles.

  @throws	invalid_argument If trying to assign a string to a
  non symbolic parameter
  @throws logic_error If the number of arguments is not equal to the number
                      of instances in this parameter
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterSetArgsDoubleValues(AMPL *ampl,
                                                          const char *name,
                                                          size_t size,
                                                          const double *args);

/**
 * Assign the specified size string values to this parameter, assigning them to
 * the parameter in the same order as the indices in the entity.
 * The number of values in the array must be equal to the
 * specified size.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of parameter as string.
 * \param	size Number of values to be assigned.
 * \param	args Values to be assigned as strings.

  @throws	invalid_argument If trying to assign a string to a
  non symbolic parameter
  @throws logic_error If the number of arguments is not equal to the number
                      of instances in this parameter
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterSetArgsStringValues(AMPL *ampl, const char *name,
                                                  size_t size,
                                                  const char * const *args);

/**
 * Assign the specified size values to this parameter, assigning them to
 * the parameter in the same order as the indices in the entity.
 * The number of values in the array must be equal to the
 * specified size.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of parameter as string.
 * \param	size Number of values to be assigned.
 * \param	args Values to be assigned as AMPL_ARGS pointer.

  @throws	invalid_argument If trying to assign a string to a
  non symbolic parameter
  @throws logic_error If the number of arguments is not equal to the number
                      of instances in this parameter
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterSetArgsValues(AMPL *ampl,
                                                    const char *name,
                                                    size_t size,
                                                    AMPL_ARGS *args);

  /**
  \rst
  Assign the specified values to a 2-d parameter, using the two dimensions
  as two indices.

  For example, the :math:`m \times n` matrix:

  .. math::

    `A = \left( \begin{array}{cccc} a_{11} & a_{12} & ... & a_{1n} \\
    a_{21} & a_{22} & ... & a_{2n} \\ ... & ... & ... & ... \\ a_{  m1} &
    a_{m2} & ... & a_{mn} \end{array} \right)`

  can be assigned to the AMPL parameter: ``param A {1..m, 1..n};``
  with the statement ``setValues(A, false)``.

  As an example, to assign the matrix:

  .. math::
    `A = \left( \begin{array}{cccc} 11 & 12  \\
    21 & 22 \\ 31 & 32 \end{array} \right)`

  to the AMPL paramater: ``param A{1..3, 1..2};`` we can use the following
  code:

  .. code-block:: ampl

    ampl.eval("param a{1..3, 1..2};");
    Parameter a = ampl.getParameter("a");

    double values[6];
    double rows[3];
    double cols[2];
    for (int i = 0; i < 3; i++) {
      rows[i] = i + 1;
      for (int j = 0; j < 2; j++)
      values[i * 2 + j] = (i + 1) * 10 + (j + 1);
    }
    for (int i = 0; i < 2; i++)
      cols[i] = i + 1;

    a.setValues(3, rows, 2, cols, values, false);

  \endrst

 * \param ampl Pointer to the AMPL struct.
 * \param name Name of the parameter.
 * \param nrows Number of rows.
 * \param row_indices Indices of the rows as AMPL_ARGS pointer.
 * \param ncols Number of columns.
 * \param col_indices Indices of the columns as AMPL_ARGS pointer.
 * \param data Values to be assigned.
 * \param transpose True to transpose the values in the matrix.

  @throws logic_error
               If the method is called on a parameter which is not
               two-dimensional
  @throws invalid_argument
              If the size of 'values' do not correspond to the sizes of
              the underlying indices
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterSetValuesMatrix(
    AMPL *ampl, const char *name, size_t nrows, AMPL_ARGS *row_indices,
    size_t ncols, AMPL_ARGS *col_indices, const double *data, bool transpose);

/**
  \rst
  Assign the values (string or double) to the parameter instances with the
  specified indices, equivalent to the AMPL code:

  .. code-block:: ampl

    let {i in indices} par[i] := values[i];

  \endrst

 * \param ampl Pointer to the AMPL struct.
 * \param name Name of the parameter.
 * \param size Number of instances to be set.
 * \param index An array of indices of the instances to be set.
 * \param v Array of values to be assigned to the instances.
 * \return Pointer to the AMPL error info struct.
 * 
 *@throws logic_error If called on a scalar parameter.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterSetSomeValues(AMPL *ampl, const char *name,
                                                   size_t size,
                                                   AMPL_TUPLE **index,
                                                   AMPL_VARIANT **v);

/**
  \rst
  Assign the values (string or double) to the parameter instances with the
  specified indices, equivalent to the AMPL code:

  .. code-block:: ampl

    let {i in indices} par[i] := values[i];

  \endrst

 * \param ampl Pointer to the AMPL struct.
 * \param name Name of the parameter.
 * \param size Number of instances to be set.
 * \param index An array of indices of the instances to be set.
 * \param args Values to be assigned to the instances.
 * \return Pointer to the AMPL error info struct.
 * 
 * @throws logic_error If called on a scalar parameter.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterSetSomeArgsValues(AMPL *ampl,
                                                       const char *name,
                                                       size_t size,
                                                       AMPL_TUPLE **index,
                                                       AMPL_ARGS *args);

/**
  \rst
  Assign the string values to the parameter instances with the
  specified indices, equivalent to the AMPL code:

  .. code-block:: ampl

    let {i in indices} par[i] := values[i];

  \endrst

 * \param ampl Pointer to the AMPL struct.
 * \param name Name of the parameter.
 * \param size Number of instances to be set.
 * \param index An array of indices of the instances to be set.
 * \param str_args String values to be assigned to the instances.
 * \return Pointer to the AMPL error info struct.
 * 
 * @throws logic_error If called on a scalar parameter.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterSetSomeStringValues(AMPL *ampl, const char *name,
                                               size_t size, AMPL_TUPLE **index,
                                               char **str_values);

/**
  \rst
  Assign the double values to the parameter instances with the
  specified indices, equivalent to the AMPL code:

  .. code-block:: ampl

    let {i in indices} par[i] := values[i];

  \endrst

 * \param ampl Pointer to the AMPL struct.
 * \param name Name of the parameter.
 * \param size Number of instances to be set.
 * \param index An array of indices of the instances to be set.
 * \param dbl_args String values to be assigned to the instances.
 * \return Pointer to the AMPL error info struct.
 * 
 * @throws logic_error If called on a scalar parameter.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterSetSomeDoubleValues(AMPL *ampl, const char *name,
                                               size_t size, AMPL_TUPLE **index,
                                               double *dbl_values);

/**@}*/


/**
 * \defgroup AMPL_VARIABLE AMPL Variable functions
 * @{
 *
 */

/**
 * Get the current value of this variable.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of variable as string.
 * \param	value Pointer to the current value.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_VariableGetValue(AMPL *ampl, const char *name,
                                              double *value);

/**
 * Fix all instances of this variable to their current value.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of variable as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_VariableFix(AMPL *ampl, const char *name);

/**
 * Fix all instances of this variable to the specified value.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of variable as string.
 * \param	value Value to fix all instances of the variable to.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_VariableFixWithValue(AMPL *ampl, const char *name,
                                                  double value);

/**
 * Unfix all instances of this variable.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of variable as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_VariableUnfix(AMPL *ampl, const char *name);

/**
 * Set all instances of this variable to the specified value.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of variable as string.
 * \param	value Value to set all instances of the variable to.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_VariableSetValue(AMPL *ampl, const char *name,
                                              double value);

/**
 * Get the integrality type for this variable.
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of variable as string.
 * \param	integrality Type of integrality (integer = 0, binary = 1,
 *                    continuous = 2).
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_VariableGetIntegrality(AMPL *ampl,
                                                    const char *name,
                                                    int *integrality);
/**@}*/

/**
 * \defgroup AMPL_CONSTRAINT AMPL Constraint functions
 * @{
 *
 */

/**
 * Check if the constraint is a logical constraint. The available suffixes
 * differ between logical and non logical constraints. See
 * https://dev.ampl.com/ampl/suffixes.html for a list of the available
 * suffixes for algebraic constraints. The suffixes available for logical
 * constraints are marked on the method description by "Valid only for logical
 * constraints".
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of constraint as string.
 * \param	isLogical True if the constraint is logical, false otherwise (pointer to bool).
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ConstraintIsLogical(AMPL *ampl, const char *name,
                                                 bool *isLogical);
                                                
/**
 * Set the value of the dual variable associated to this constraint (valid only if the constraint is scalar).
 * Equivalent to the AMPL statement:
 * code: `let name := dual;`
 * Note that dual values are often reset by the underlying AMPL interpreter by the presolve functionalities triggered by some methods. 
 * A possible workaround is to set the option presolve to false (see AMPL_SetDblOption).
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of constraint as string.
 * \param	dual Value to set the dual variable to.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ConstraintSetDual(AMPL *ampl, const char *name,
                                               double dual);
/**@}*/

/**
 * \defgroup AMPL_OBJECTIVE AMPL Objective functions
 * @{
 *
 */

/**
 * Get the sense of this objective.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of objective as string.
 * \param sense 0 if maximize, else minimize (pointer to int).
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ObjectiveSense(AMPL *ampl, const char *name,
                                            int *sense);

/**@}*/

/**
 * \defgroup AMPL_SET AMPL Set functions
 * @{
 *
 */

/**
 * The arity of this set, or number of components in each member of this set.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of set as string.
 * \param	arity Pointer to the arity of the set.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetGetArity(AMPL *ampl, const char *name,
                                         size_t *arity);

/**@}*/


/**
 * \defgroup AMPL_TABLE AMPL Table functions
 * @{
 *
 */

/**
 * Read from the table (equivalent to the %AMPL code `read table name;`).
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of table as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_TableRead(AMPL *ampl, const char *name);

/**
 * Write to the table (equivalent to the %AMPL code `write table name;`)-
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of table as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_TableWrite(AMPL *ampl, const char *name);

/**@}*/


/**
 * \defgroup AMPL_INSTANCE AMPL Instance functions
 * @{
 *
 */

/**
 * Get a double suffix value of this instance.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	entityname Name of instance as string.
 * \param	suffix Numeric suffix to get.
 * \param	value Pointer to the value of the suffix.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_InstanceGetDoubleSuffix(AMPL *ampl,
                                                     const char *entityname,
                                                     AMPL_TUPLE *tuple,
                                                     AMPL_NUMERICSUFFIX suffix,
                                                     double *value);

/**
 * Get a integer suffix value of this instance.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	entityname Name of instance as string.
 * \param	suffix Numeric suffix to get.
 * \param	value Pointer to the value of the suffix.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_InstanceGetIntSuffix(AMPL *ampl, const char *entityname,
                                                  AMPL_TUPLE *tuple,
                                                  AMPL_NUMERICSUFFIX suffix,
                                                  int *value);

/**
 * Get a string suffix value of this instance.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	entityname Name of instance as string.
 * \param	suffix String suffix to get.
 * \param	value Pointer to the value of the suffix.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_InstanceGetStringSuffix(AMPL *ampl,
                                                     const char *entityname,
                                                     AMPL_TUPLE *tuple,
                                                     AMPL_STRINGSUFFIX suffix,
                                                     char **value);
/**
 * Get a double custom suffix value of this instance.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	entityname Name of instance as string.
 * \param	tuple Index of instance as tuple.
 * \param	suffix String suffix to get.
 * \param	value Pointer to the value of the suffix.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_InstanceGetUserDefinedDoubleSuffix(AMPL *ampl, const char *entityname,
                                                           AMPL_TUPLE *tuple, const char *suffix,
                                                           double *value);

/**
 * Get a string custom suffix value of this instance.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	entityname Name of instance as string.
 * \param	tuple Index of instance as tuple.
 * \param	suffix String suffix to get.
 * \param	value Pointer to the value of the suffix.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_InstanceGetUserDefinedStringSuffix(AMPL *ampl, const char *entityname,
                                                            AMPL_TUPLE *tuple, const char *suffix,
                                                            char **value);

AMPLAPI AMPL_ERRORINFO *AMPL_InstanceSetDoubleSuffix(AMPL *ampl, const char *entityname,
                                                     AMPL_TUPLE *tuple, const char *suffix,
                                                     double value);

AMPLAPI AMPL_ERRORINFO *AMPL_InstanceSetStringSuffix(AMPL *ampl, const char *entityname,
                                                     AMPL_TUPLE *tuple, const char *suffix,
                                                     const char *value);

/**
 * Get name of instance.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	entityname Name of entity as string.
 * \param	tuple Tuple of indices of the instance.
 * \param	name Pointer to the name of the instance.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_InstanceGetName(AMPL *ampl, const char *entityname,
                                             AMPL_TUPLE *tuple, char **name);

/**
 * Returns a string representation of this instance.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of instance as string.
 * \param	str Pointer to the string representation of the instance.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_InstanceToString(AMPL *ampl, const char *entityname,
                                              AMPL_TUPLE *tuple,
                                              char **str);

/**
 * Drop this instance, corresponding to the %AMPL code:
 * `drop name;`.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of instance as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_InstanceDrop(AMPL *ampl, const char *entityname, AMPL_TUPLE *tuple);

/**
 * Restore this instance, corresponding to the
 * %AMPL code: `restore name;`.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of instance as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_InstanceRestore(AMPL *ampl, const char *entityname, AMPL_TUPLE *tuple);

/**@}*/

/**
 * \defgroup AMPL_VARIABLEINSTANCE AMPL Variable Instance functions
 * @{
 *
 */

/**
 * Fix this variable instance to their current value.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of variable instance as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_VariableInstanceFix(AMPL *ampl, const char *entityname, AMPL_TUPLE *tuple);

/**
 * Fix this variable instance to the specified value.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of variable instance as string.
 * \param	value Value to fix the variable instance to.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_VariableInstanceFixToValue(AMPL *ampl,
                                                        const char *entityname,
                                                        AMPL_TUPLE *tuple,
                                                        double value);

/**
 * Unfix this variable instance.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of variable instance as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_VariableInstanceUnfix(AMPL *ampl,
                                                   const char *entityname,
                                                   AMPL_TUPLE *tuple);

/**
 * Set the current value of this variable instance (does not fix it),
 * equivalent to the %AMPL command `let`.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of variable instance as string.
 * \param value Value to set the variable instance to.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_VariableInstanceSetValue(AMPL *ampl,
                                                      const char *entityname,
                                                      AMPL_TUPLE *tuple,
                                                      double value);

/**
 * Returns a string representation of this variable instance.
 * The format is as follows:
 *
 * \rst
 * ::
 *   'var' name attrs ';'
 * \endrst
 *
 * where ``name`` is the variable instance name method and ``attrs``
 * represent attributes similar to those used in variable declarations.
 * <p>
 * If the lower bound (``lb``) is equal to the upper bound (``ub``), the
 * attributes contain ``= lb``.
 * <p>
 * If the lower bound is not equal to the upper bound and
 * ``Double.NEGATIVE_INFINITY`` , the attributes contain ``>= lb``.
 * <p>
 * If the upper bound is not equal to the lower bound and
 * ``Double.POSITIVE_INFINITY``, the attributes contain ``<= ub``.
 *
 * <p>
 * If the variable is integer, the attributes contain ``integer``.
 * <p>
 * If the variable is binary, the attributes contain ``binary``.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of variable instance as string.
 * \param	entityname Name of entity as string.
 * \param	str Pointer to the string representation of the variable instance.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_VariableInstanceToString(AMPL *ampl,
                                                      const char *entityname,
                                                      AMPL_TUPLE *tuple,
                                                      char **str);

/**@}*/

/**
 * \defgroup AMPL_CONSTRAINTINSTANCE AMPL Constraint Instance functions
 * @{
 *
 */

/**
 * Set the value of the dual variable associated to this constraint.
 * Equivalent to the %AMPL statement:
 *
 * `let c := dual;`
 *
 * Note that dual values are often reset by the underlying %AMPL interpreter
 * by the presolve functionalities triggered by some methods. A possible
 * workaround is to set the option `presolve` to `0.0` (see AMPL_SetDblOption()).
 *
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of constraint instance as string.
 * \param dual The value to be assigned to the dual variable.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ConstraintInstanceSetDual(AMPL *ampl,
                                                       const char *entityname,
                                                       AMPL_TUPLE *tuple,
                                                       double dual);

/**@}*/

/**
 * \defgroup AMPL_SETINSTANCE AMPL Set Instance functions
 * @{
 *
 */

/**
 * Get the number of tuples in this set instance.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of set instance as string.
 * \param	size Pointer to the number of tuples in the set instance.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetInstanceGetSize(AMPL *ampl, const char *entityname,
                                                AMPL_TUPLE *tuple,
                                                size_t *size);

/**
 * Check wether this set instance contains the specified tuple.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of set instance as string.
 * \param tuple Pointer to the tuple to be found.
 * \param contains True if the set instance contains the tuple, false otherwise (pointer to bool).
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetInstanceContains(AMPL *ampl, const char *entityname,
                                                 AMPL_TUPLE *index,
                                                 AMPL_TUPLE *tuple,
                                                 bool *contains);

/**
 * Get the values of this set instance as tuples.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of set instance as string.
 * \param tuples Pointer to the tuples that represents the values.
 * \param size Pointer to the number of tuples in the set instance.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetInstanceGetValues(AMPL *ampl, const char *entityname,
                                                  AMPL_TUPLE *tuple,
                                                  AMPL_TUPLE ***tuples,
                                                  size_t *size);

/**
 * Get the values of this set instance in a Dataframe.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of set instance as string.
 * \param dataframe Pointer to the dataframe that represents the values.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetInstanceGetValuesDataframe(
    AMPL *ampl, const char *entityname, AMPL_TUPLE *tuple, AMPL_DATAFRAME **dataframe);

AMPLAPI AMPL_ERRORINFO *AMPL_SetInstanceGetValuesArrow(AMPL *ampl, const char *entityname, AMPL_TUPLE *tuple,
                                               struct AMPL_DataFrameArrow **dataframe_arrow);

/**
 * Set the values of this set instance with AMPL_ARGS.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of set instance as string.
 * \param entityname Name of entity as string.
 * \param args Pointer to the arguments that represents the values.
 * \param size Pointer to the number of arguments in the set instance.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetInstanceSetValues(AMPL *ampl, const char *entityname,
                                                  AMPL_TUPLE *tuple,
                                                  AMPL_ARGS *args, size_t size);

/**
 * Set the values of this set instance using tuples.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of set instance as string.
 * \param entityname Name of entity as string.
 * \param tuples Pointer to the tuples that represents the values.
 * \param size Pointer to the number of tuples in the set instance.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetInstanceSetValuesTuples(AMPL *ampl,
                                                        const char *entityname,
                                                        AMPL_TUPLE *tuple,
                                                        AMPL_TUPLE **tuples,
                                                        size_t size);

/**
 * Set the values of this set instance using a Dataframe.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of set instance as string.
 * \param entityname Name of entity as string.
 * \param data Pointer to the dataframe that represents the values.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetInstanceSetValuesDataframe(
    AMPL *ampl, const char *entityname, AMPL_TUPLE *tuple, AMPL_DATAFRAME *data);

AMPLAPI AMPL_ERRORINFO *AMPL_SetInstanceSetValuesArrow(AMPL *ampl, const char *entityname, AMPL_TUPLE *tuple, 
                                                       AMPL_DATAFRAMEARROW *dataframe);

/**
 * Returns a string representation of this set instance.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of set instance as string.
 * \param str Pointer to the string representation of the set instance.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_SetInstanceToString(AMPL *ampl, const char *entityname,
                                                 AMPL_TUPLE *tuple,
                                                 char **str);

/**@}*/

/**
 * \defgroup AMPL_PARAMETERINSTANCE AMPL Parameter Instance functions
 * @{
 *
 */

/**
 * Set the value of a single instance of this parameter.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of parameter instance as string.
 * \param	index Tuple of indices of the instance.
 * \param	v Pointer to the value to set the parameter instance to.
 * \return Pointer to the AMPL error info struct.
 * 
 * @throws runtime_error
 *            if the entity has been deleted in the underlying %AMPL
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterInstanceSetValue(AMPL *ampl, const char *name,
                                                  AMPL_TUPLE *index,
                                                  AMPL_VARIANT *v);

/**
 * Set the double value of a single instance of this parameter.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of parameter instance as string.
 * \param	index Tuple of indices of the instance.
 * \param	value Double value to set the parameter instance to.
 * \return Pointer to the AMPL error info struct.
 * 
 * @throws runtime_error
 *            if the entity has been deleted in the underlying %AMPL
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterInstanceSetNumericValue(AMPL *ampl,
                                                         const char *name,
                                                         AMPL_TUPLE *index,
                                                         double value);

/**
 * Set the string value of a single instance of this parameter.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of parameter instance as string.
 * \param	index Tuple of indices of the instance.
 * \param	value Stringvalue to set the parameter instance to.
 * \return Pointer to the AMPL error info struct.
 * 
 * @throws runtime_error
 *            if the entity has been deleted in the underlying %AMPL
 */
AMPLAPI AMPL_ERRORINFO *AMPL_ParameterInstanceSetStringValue(AMPL *ampl,
                                                        const char *name,
                                                        AMPL_TUPLE *index,
                                                        const char *value);

/**@}*/

/**
 * \defgroup AMPL_TABLEINSTANCE AMPL Table Instance functions
 * @{
 *
 */

/**
 * Read the current table instance, corresponding to the %AMPL code:
 * `read table tablename[tableindex];`.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of table instance as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_TableInstanceRead(AMPL *ampl, const char *entityname, AMPL_TUPLE *tuple);

/**
 * Write the current table instance, corresponding to the %AMPL code:
 * `write table tablename[tableindex];`.
 * 
 * \param	ampl Pointer to the AMPL struct.
 * \param	name Name of table instance as string.
 * \return Pointer to the AMPL error info struct.
 */
AMPLAPI AMPL_ERRORINFO *AMPL_TableInstanceWrite(AMPL *ampl, const char *entityname, AMPL_TUPLE *tuple);

/**@}*/

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif  // AMPL_AMPL_C_H
