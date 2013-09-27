#ifndef _GTP_PLUGIN_H_
#define _GTP_PLUGIN_H_

/* Follow part for ARCH.  */
#ifdef CONFIG_X86
#define ULONGEST		uint64_t
#define LONGEST			int64_t
#define CORE_ADDR		unsigned long

#if (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,24))
#define GTP_REGS_PC(regs)	((regs)->ip)
#else
#ifdef CONFIG_X86_32
#define GTP_REGS_PC(regs)	((regs)->eip)
#else
#define GTP_REGS_PC(regs)	((regs)->rip)
#endif
#endif

#ifdef CONFIG_X86_32
#define GTP_REG_ASCII_SIZE	128
#define GTP_REG_BIN_SIZE	64

#define GTP_SP_NUM		4
#define GTP_PC_NUM		8
#else
#define GTP_REG_ASCII_SIZE	296
#define GTP_REG_BIN_SIZE	148

#define GTP_SP_NUM		7
#define GTP_PC_NUM		16
#endif

#define GTP_X86_NEED_ADJUST_PC(gts)	(!(gts)->step && !(gts)->hwb && (gts)->tpe->type != gtp_entry_uprobe)
#endif

#ifdef CONFIG_MIPS
#define ULONGEST		uint64_t
#define LONGEST			int64_t
#define CORE_ADDR		unsigned long

#define GTP_REGS_PC(regs)	((regs)->cp0_epc)

#ifdef CONFIG_32BIT
#define GTP_REG_ASCII_SIZE	304
#define GTP_REG_BIN_SIZE	152
#else
#define GTP_REG_ASCII_SIZE	608
#define GTP_REG_BIN_SIZE	304
#endif

#define GTP_SP_NUM		29
#define GTP_PC_NUM		37
#endif

#ifdef CONFIG_ARM
#define ULONGEST		uint64_t
#define LONGEST			int64_t
#define CORE_ADDR		unsigned long

#define GTP_REGS_PC(regs)	((regs)->uregs[15])

#define GTP_REG_ASCII_SIZE	336
#define GTP_REG_BIN_SIZE	168

#define GTP_SP_NUM		13
#define GTP_PC_NUM		15
#endif

struct gtp_var;

struct gtp_trace_s {
	struct gtp_entry		*tpe;
	struct pt_regs			*regs;

#ifdef CONFIG_X86_32
#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,26))
	unsigned long			x86_32_sp;
#else
	long				x86_32_sp;
#endif
#endif

	long				(*read_memory)(void *dst,
						       void *src,
						       size_t size);
#ifdef GTP_FRAME_SIMPLE
	/* Next part set it to prev part.  */
	char				**next;
#endif
#ifdef GTP_FTRACE_RING_BUFFER
	/* NULL means doesn't have head.  */
	char				*next;
#endif
#ifdef GTP_RB
	/* rb of current cpu.  */
	struct gtp_rb_s			*next;
	u64				id;
#endif

	/* Not 0 if this is step action.
	   Its value is step number that need exec (include current step).
	   For example, if a tracepoint have 1 step,
	   its step action gts->step will be 1.  */
	int				step;

	struct kretprobe_instance	*ri;
	int				*run;
	struct timespec			xtime;

	/* $watch_id will set to WATCH_TPE.  */
	struct gtp_entry		*watch_tpe;
	/* $watch_type will set to WATCH_TYPE.  */
	int				watch_type;
	/* $watch_size will set to WATCH_SIZE.  */
	int				watch_size;
	/* The return of $watch_start or $watch_stop.
	   0 is success.  */
	int				watch_start_ret;
	int				watch_stop_ret;

	/* If this is a session is for a hardware breakpoint.
	   HWB point to the struct.
	   If not, it will set to NULL.  */
	struct gtp_hwb_s		*hwb;
	/* hwb_current_val have the value of hwb address watch
	   when hwb_current_val_gotten is true.  */
	int64_t				hwb_current_val;
	int				hwb_current_val_gotten;

	/* For set $current.  */
	struct pt_regs			*tmp_regs;

	int64_t				printk_tmp;
	unsigned int			printk_level;
	unsigned int			printk_format;
	struct gtpsrc			*printk_str;
};

struct gtp_var_hooks {
	int	(*gdb_set_val)(struct gtp_trace_s *unused, struct gtp_var *var,
			       int64_t val);
	int	(*gdb_get_val)(struct gtp_trace_s *unused, struct gtp_var *var,
			       int64_t *val);
	int	(*agent_set_val)(struct gtp_trace_s *gts, struct gtp_var *var,
				 int64_t val);
	int	(*agent_get_val)(struct gtp_trace_s *gts, struct gtp_var *var,
				 int64_t *val);
};

extern int gtp_plugin_mod_register(struct module *mod);
extern int gtp_plugin_mod_unregister(struct module *mod);

extern struct gtp_var *gtp_plugin_var_add(char *name, int64_t val,
					  struct gtp_var_hooks *hooks);
extern int gtp_plugin_var_del(struct gtp_var *var);

extern ULONGEST gtp_action_reg_read(struct gtp_trace_s *gts, int num);

#endif /* _GTP_PLUGIN_H_ */
