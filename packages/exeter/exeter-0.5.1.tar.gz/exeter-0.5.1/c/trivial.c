// SPDX-License-Identifier: MIT

/*
 * Copyright Red Hat
 * Author: David Gibson <david@gibson.dropbear.id.au>
 */

#include <stdlib.h>

#include "exeter.h"

static void trivial_pass(void)
{
}

static void trivial_fail(void)
{
	abort();
}

static void trivial_skip(void)
{
	exeter_skip("This test is trivially skipped");
}

int main(int argc, char *argv[])
{
	struct exeter_testcase *c;

	c = exeter_register("trivial_pass", trivial_pass);
	exeter_set_description(c, "Trivially pass");
	c = exeter_register("trivial_fail", trivial_fail);
	exeter_set_description(c, "Trivially fail");
	c = exeter_register("trivial_skip", trivial_skip);
	exeter_set_description(c, "Trivially skip");

	exeter_main(argc, argv);
}
