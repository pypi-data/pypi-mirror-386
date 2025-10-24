// SPDX-License-Identifier: MIT

/*
 * Copyright Red Hat
 * Author: David Gibson <david@gibson.dropbear.id.au>
 */

#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "exeter.h"

#define TESTID_CHARS	\
	"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.;_"

/* Exit codes for exeter protocol */
#define EXIT_PASS		EXIT_SUCCESS
#define EXIT_SKIP		77
#define EXIT_HARD_FAILURE	99

struct exeter_testcase {
	const char *id;
	exeter_testfn_t fn;
	const char *description;
	struct exeter_testcase *next;
};
static struct exeter_testcase *manifest; /* = NULL */

static void *xmalloc(size_t size)
{
	void *p = malloc(size);

	if (!p) {
		fprintf(stderr, "exeter (c): Out of memory\n");
		exit(EXIT_HARD_FAILURE);
	}

	return p;
}

static char *xstrdup(const char *s)
{
	char *p = strdup(s);

	if (!p) {
		fprintf(stderr, "exeter (c): Out of memory\n");
		exit(EXIT_HARD_FAILURE);
	}

	return p;
}

struct exeter_testcase *exeter_testcase(const char *testid)
{
	struct exeter_testcase *c;

	for (c = manifest; c; c = c->next) {
		if (strcmp(testid, c->id) == 0)
			return c;
	}

	return NULL;
}

const char *exeter_testcase_id(struct exeter_testcase *c)
{
	return c->id;
}

static void check_testid(const char *id)
{
	if (strlen(id) == 0 || strspn(id, TESTID_CHARS) != strlen(id)) {
		fprintf(stderr, "exeter(C): Bad test id \"%s\"\n", id);
		exit(EXIT_HARD_FAILURE);
	}
}

struct exeter_testcase *exeter_register(const char *id, exeter_testfn_t fn)
{
	struct exeter_testcase *new;

	check_testid(id);

	new = xmalloc(sizeof(*new));

	new->id = xstrdup(id);
	new->fn = fn;
	new->description = NULL;
	new->next = manifest;
	manifest = new;

	return new;
}

void exeter_set_description(struct exeter_testcase *c, const char *description)
{
	c->description = xstrdup(description);
}

static void usage(const char *exename, FILE *f)
{
	fprintf(f, "Usage: %s [OPTIONS] <testcase id>\n", exename);
	fprintf(f, "\n");
	fprintf(f, "Exeter (C) based tests.\n");
	fprintf(f, "\n");
	fprintf(f, "Options:\n");
	fprintf(f, "    --exeter         display protocol version and exit\n");
	fprintf(f, "    --help           display this help and exit\n");
	fprintf(f, "    --list           list test cases and exit\n");
	fprintf(f, "    --metadata <id>  output metadata for test case and exit\n");
}

_Noreturn void exeter_skip(const char *reason)
{
	if (reason)
		printf("SKIP: %s\n", reason);
	exit(EXIT_SKIP);
}

static void exeter_list(int argc, char *argv[])
{
	const struct exeter_testcase *c;

	if (argc) {
		int i;

		for (i = 0; i < argc; i++) {
			c = exeter_testcase(argv[i]);
			if (!c) {
				fprintf(stderr, "exeter (c): Nonexistent test %s\n", argv[i]);
				exit(EXIT_HARD_FAILURE);
			}
			printf("%s\n", c->id);
		}
	} else {
		for (c = manifest; c; c = c->next)
			printf("%s\n", c->id);
	}
}

static void encode_value(const char *value)
{
	const char *p;

	for (p = value; *p; p++) {
		switch (*p) {
		case '\\':
			printf("\\\\");
			break;
		case '\n':
			printf("\\n");
			break;
		case '\0':
			printf("\\0");
			break;
		default:
			putchar(*p);
			break;
		}
	}
}

static void exeter_metadata(const char *testid)
{
	const struct exeter_testcase *c = exeter_testcase(testid);

	if (!c) {
		fprintf(stderr, "exeter (c): Nonexistent test %s\n", testid);
		exit(EXIT_HARD_FAILURE);
	}

	if (c->description) {
		printf("description=");
		encode_value(c->description);
		printf("\n");
	}
}


static void exeter_run(const char *testid)
{
	const struct exeter_testcase *c;

	check_testid(testid);

	printf("exeter (c): Running test %s\n", testid);

	c = exeter_testcase(testid);
	if (!c) {
		fprintf(stderr, "exeter (c): Nonexistent test %s\n", testid);
		exit(EXIT_HARD_FAILURE);
	}
	c->fn();
}

_Noreturn void exeter_main(int argc, char *argv[])
{
	const char *exename = argv[0];

	if (argc < 2) {
		usage(exename, stdout);
		exit(EXIT_PASS);
	} else {
		const char *testid = argv[1];

		if (strcmp(testid, "--exeter") == 0) {
			printf("exeter test protocol 0.4.1\n");
			exit(EXIT_PASS);
		} else if (strcmp(testid, "--help") == 0) {
			usage(exename, stdout);
			exit(EXIT_PASS);
		} else if (strcmp(testid, "--list") == 0) {
			exeter_list(argc - 2, argv + 2);
			exit(EXIT_PASS);
		} else if (strcmp(testid, "--metadata") == 0) {
			if (argc != 3) {
				usage(argv[0], stderr);
				exit(EXIT_HARD_FAILURE);
			}
			exeter_metadata(argv[2]);
			exit(EXIT_PASS);
		} else {
			if (argc == 2) {
				exeter_run(testid);
				exit(EXIT_PASS);
			}
		}
	}

	usage(argv[0], stderr);

	exit(EXIT_HARD_FAILURE);
}
