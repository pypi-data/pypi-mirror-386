// SPDX-License-Identifier: MIT
/*
 * Copyright Red Hat
 * Author: David Gibson <david@gibson.dropbear.id.au>
 */

#ifndef _EXETER_H
#define _EXETER_H 1

#include "config.h"

/* exeter_testfn_t - Function pointer type for test functions.
 *
 * Test functions take no parameters and return void.
 */
typedef void (*exeter_testfn_t)(void);

/* struct exeter_testcase - A single exeter test case */
struct exeter_testcase;

/* exeter_register() - Register a test case with the exeter framework
 * @id:	Unique test identifier (alphanumeric, dots, semicolons, underscores)
 * @fn:	Test function to execute
 * Returns: Pointer to registered test case, exits on error
 */
struct exeter_testcase *exeter_register(const char *id, exeter_testfn_t fn);

/* exeter_set_description() - Set description for a registered test case
 * @c:		Test case pointer
 * @description:	Human-readable test description
 */
void exeter_set_description(struct exeter_testcase *c, const char *description);

/* exeter_testcase() - Look up a registered test case by ID
 * @id:	Test identifier to find
 * Returns: Pointer to test case, or NULL if not found
 */
struct exeter_testcase *exeter_testcase(const char *id);

/* exeter_testcase_id() - Return ID of an exeter testcase
 * @c:	Test case pointer
 * Returns: Exeter test ID
 */
const char *exeter_testcase_id(struct exeter_testcase *c);

/*
 * exeter_skip() - Skip the current test
 * @reason:	Reason for skipping
 *
 * Skips this test by exiting with code 77.
 */
_Noreturn void exeter_skip(const char *reason);

/*
 * exeter_main() - Entry point for exeter test programs
 * @argc:	Argument count from main()
 * @argv:	Argument vector from main()
 *
 * Implements exeter test protocol, according to given command line.
 * This function always exits and never returns.
 */
_Noreturn void exeter_main(int argc, char *argv[]);


#endif /* _EXETER_H */
