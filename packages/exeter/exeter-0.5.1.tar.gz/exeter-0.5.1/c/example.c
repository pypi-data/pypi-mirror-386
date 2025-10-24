// SPDX-License-Identifier: MIT

/*
 * Copyright Red Hat
 * Author: David Gibson <david@gibson.dropbear.id.au>
 */

#include <assert.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "exeter.h"

static void nop_pass(void)
{
}

static void exit_pass(void)
{
	exit(0);
}

static void assert_pass(void)
{
	assert(1);
}

static void exit_fail(void)
{
	exit(1);
}

static void assert_fail(void)
{
	assert(0);
}

static void abort_fail(void)
{
	abort();
}

static void kill_fail(void)
{
	kill(getpid(), SIGTERM);
}

static void null_deref_fail(void)
{
	printf("%c\n", *((char *)NULL));
}

int main(int argc, char *argv[])
{
	struct exeter_testcase *c;

	c = exeter_register("nop_pass", nop_pass);
	exeter_set_description(c, "Do nothing");

	c = exeter_register("exit_pass", exit_pass);
	exeter_set_description(c, "exit(0)");

	c = exeter_register("assert_pass", assert_pass);
	exeter_set_description(c, "assert(1)");

	c = exeter_register("exit_fail", exit_fail);
	exeter_set_description(c, "Fail by exit(1)");

	c = exeter_register("assert_fail", assert_fail);
	exeter_set_description(c, "Fail by assert(0)");

	c = exeter_register("abort_fail", abort_fail);
	exeter_set_description(c, "Fail by abort()");

	c = exeter_register("kill_fail", kill_fail);
	exeter_set_description(c, "Fail by killing self with SIGTERM");

	c = exeter_register("null_deref_fail", null_deref_fail);
	exeter_set_description(c, "Fail by dereferencing NULL");

	exeter_main(argc, argv);
}
