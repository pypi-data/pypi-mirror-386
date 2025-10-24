// SPDX-License-Identifier: MIT

/*
 * Copyright Red Hat
 * Author: David Gibson <david@gibson.dropbear.id.au>
 */

#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "exeter.h"

static void dummy_test(void)
{
}

static void test_register_return(void)
{
	struct exeter_testcase *c;

	c = exeter_register("dummy", dummy_test);
	assert(c != NULL);
	printf("exeter_register returns non-NULL handle\n");
}

static void test_get_case_exists(void)
{
	struct exeter_testcase *c1, *c2;

	c1 = exeter_register("test_case", dummy_test);
	c2 = exeter_testcase("test_case");
	
	assert(c1 == c2);
	printf("exeter_testcase finds registered case\n");
}

static void test_get_case_missing(void)
{
	struct exeter_testcase *c;

	c = exeter_testcase("nonexistent");
	assert(c == NULL);
	printf("exeter_testcase returns NULL for missing case\n");
}

static void test_case_id(void)
{
	struct exeter_testcase *c;
	const char *id;

	c = exeter_register("my_test", dummy_test);
	id = exeter_testcase_id(c);
	
	assert(id != NULL);
	assert(strcmp(id, "my_test") == 0);
	printf("exeter_testcase_id returns correct ID\n");
}

int main(int argc, char *argv[])
{
	exeter_register("test_register_return", test_register_return);
	exeter_register("test_get_case_exists", test_get_case_exists);
	exeter_register("test_get_case_missing", test_get_case_missing);
	exeter_register("test_case_id", test_case_id);

	exeter_main(argc, argv);
}
