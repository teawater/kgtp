#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/version.h>
#include <linux/err.h>

#include "gtp.h"

/* This include just for sprint_backtrace.  */
#include <linux/kallsyms.h>

static void plugin_example_exit(void);

struct gtp_var	*test1 = NULL, *test2 = NULL, *test3 = NULL, *test4 = NULL;

static int64_t	test2_val = 20;

static int
test2_hooks_get_val(struct gtp_trace_s *unused1, struct gtp_var *unused2,
	            int64_t *val)
{
	*val = test2_val;
	return 0;
}

static int
test2_hooks_set_val(struct gtp_trace_s *unused1,
		    struct gtp_var *unused2, int64_t val)
{
	test2_val = val;
	return 0;
}

static struct gtp_var_hooks	test2_hooks = {
	.gdb_get_val = test2_hooks_get_val,
	.gdb_set_val = test2_hooks_set_val,
	.agent_get_val = test2_hooks_get_val,
	.agent_set_val = test2_hooks_set_val,
};

static int
test3_hooks_set_val(struct gtp_trace_s *unused1,
		    struct gtp_var *unused2, int64_t val)
{
	char	sym[KSYM_SYMBOL_LEN];

	sprint_symbol(sym, (unsigned long)val);
	printk(KERN_WARNING "<%lu> %s\n", (unsigned long)val, sym);
	return 0;
}

static struct gtp_var_hooks	test3_hooks = {
	.agent_set_val = test3_hooks_set_val,
};

static int
test4_hooks_set_val(struct gtp_trace_s *gts,
		    struct gtp_var *unused, int64_t val)
{
	char		sym[KSYM_SYMBOL_LEN];
	unsigned long	addr = (unsigned long)gtp_action_reg_read(gts,
								  GTP_PC_NUM);

	sprint_symbol(sym, (unsigned long)addr);
	printk(KERN_WARNING "<%lu> %s\n", (unsigned long)addr, sym);
	return 0;
}

static struct gtp_var_hooks	test4_hooks = {
	.agent_set_val = test4_hooks_set_val,
};

static int
plugin_example_init(void)
{
	int		ret = 0;

	ret = gtp_plugin_mod_register(THIS_MODULE);
	if (ret)
		return ret;

	test1 = gtp_plugin_var_add("test1", 10, NULL);
	if (IS_ERR(test1)) {
		ret = PTR_ERR(test1);
		test1 = NULL;
		goto out;
	}
	test2 = gtp_plugin_var_add("test2", test2_val, &test2_hooks);
	if (IS_ERR(test2)) {
		ret = PTR_ERR(test2);
		test2 = NULL;
		goto out;
	}
	/* Action example:
	   teval $test3=(int64_t)$rip */
	test3 = gtp_plugin_var_add("test3", 0, &test3_hooks);
	if (IS_ERR(test3)) {
		ret = PTR_ERR(test3);
		test3 = NULL;
		goto out;
	}
	test4 = gtp_plugin_var_add("test4", 0, &test4_hooks);
	if (IS_ERR(test4)) {
		ret = PTR_ERR(test4);
		test4 = NULL;
		goto out;
	}

out:
	if (ret != 0)
		plugin_example_exit();
	return ret;
}

static void
plugin_example_exit(void)
{
	if (test1)
		gtp_plugin_var_del(test1);
	if (test2)
		gtp_plugin_var_del(test2);
	if (test3)
		gtp_plugin_var_del(test3);
	if (test4)
		gtp_plugin_var_del(test4);

	gtp_plugin_mod_unregister(THIS_MODULE);
}

module_init(plugin_example_init)
module_exit(plugin_example_exit)

MODULE_LICENSE("GPL");
