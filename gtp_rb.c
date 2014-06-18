/*
 * Ring buffer of kernel GDB tracepoint module.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 *
 * Copyright(C) KGTP team (https://code.google.com/p/kgtp/), 2011, 2012
 *
 */

/* Following macros is for page of ring buffer.  */
#define ADDR_SIZE		sizeof(size_t)
#define GTP_RB_HEAD(addr)	((void *)((size_t)(addr) & PAGE_MASK))
#define GTP_RB_DATA(addr)	(GTP_RB_HEAD(addr) + ADDR_SIZE)
#define GTP_RB_END(addr)	(GTP_RB_HEAD(addr) + PAGE_SIZE - ADDR_SIZE)
#define GTP_RB_PREV(addr)	(*(void **)GTP_RB_HEAD(addr))
#define GTP_RB_NEXT(addr)	(*(void **)GTP_RB_END(addr))
#define GTP_RB_DATA_MAX		(PAGE_SIZE - ADDR_SIZE - ADDR_SIZE - FID_SIZE \
				 - sizeof(u64))

struct gtp_rb_s {
	spinlock_t	lock;

	/* Pointer to the prev frame entry head.
	   */
	void		*prev_frame;

	/* When write, this is the next address to be write.
	   When read, this is the end of read.  */
	void		*w;

	/* When alloc memory from rb, record prev value W to PREV_W.
	   When this memory doesn't need, set W back to PREV_W to release
	   this memroy.  */
	void		*prev_w;

	/* Point to the begin of ring buffer.  Read will begin from R.  */
	void		*r;

	/* Point to the trace frame entry head of current read.  */
	void		*rp;

	/* This the id of rp point to.
	   0 means rp doesn't point to a trace frame entry.
	   So it need call gtp_rb_walk first.  */
	u64		rp_id;

	/* The cpu id.  */
	int		cpu;
};

static struct gtp_rb_s __percpu	*gtp_rb;
#if defined(CONFIG_ARM) && (LINUX_VERSION_CODE < KERNEL_VERSION(2,6,34))
static atomic_t				gtp_rb_count;
#else
static atomic64_t			gtp_rb_count;
#endif
static unsigned int		gtp_rb_page_count;
static atomic_t			gtp_rb_discard_page_number;

static int
gtp_rb_init(void)
{
	int	cpu;

	gtp_rb = alloc_percpu(struct gtp_rb_s);
	if (!gtp_rb)
		return -ENOMEM;

	for_each_online_cpu(cpu) {
		struct gtp_rb_s	*rb
			= (struct gtp_rb_s *)per_cpu_ptr(gtp_rb, cpu);
		memset(rb, 0, sizeof(struct gtp_rb_s));
		rb->lock = __SPIN_LOCK_UNLOCKED(rb->lock);
		rb->cpu = cpu;
	}
	gtp_rb_page_count = 0;
	atomic_set(&gtp_rb_discard_page_number, 0);

	return 0;
}

static void
gtp_rb_release(void)
{
	if (gtp_rb) {
		free_percpu(gtp_rb);
		gtp_rb = NULL;
	}
}

static void
gtp_rb_reset(void)
{
	int	cpu;

	for_each_online_cpu(cpu) {
		struct gtp_rb_s	*rb
			= (struct gtp_rb_s *)per_cpu_ptr(gtp_rb, cpu);
		rb->w = GTP_RB_DATA(rb->w);
		rb->r = rb->w;
		rb->rp = NULL;
		rb->rp_id = 0;
		rb->prev_frame = NULL;
	}

#if defined(CONFIG_ARM) && (LINUX_VERSION_CODE < KERNEL_VERSION(2,6,34))
	atomic_set(&gtp_rb_count, 0);
#else
	atomic64_set(&gtp_rb_count, 0);
#endif
	atomic_set(&gtp_rb_discard_page_number, 0);
}

static inline u64
gtp_rb_clock(void)
{
	u64	ret;

re_inc:
#if defined(CONFIG_ARM) && (LINUX_VERSION_CODE < KERNEL_VERSION(2,6,34))
	ret = (u64)atomic_inc_return(&gtp_rb_count);
#else
	ret = atomic64_inc_return(&gtp_rb_count);
#endif
	if (ret == 0)
		goto re_inc;

	return ret;
}

#define GTP_RB_PAGE_IS_EMPTY	(gtp_rb_page_count == 0)

static int
gtp_rb_page_alloc(int size)
{
	int	cpu;

	for_each_online_cpu(cpu) {
		struct gtp_rb_s	*rb
			= (struct gtp_rb_s *)per_cpu_ptr(gtp_rb, cpu);
		void		*last = NULL, *next = NULL;
		struct page	*page;
		int		current_size;

		gtp_rb_page_count = 0;
		current_size = size;

		while (1) {
			if (current_size > 0)
				current_size -= PAGE_SIZE;
			else
				break;

			page = alloc_pages_node(cpu_to_node(cpu),
						GFP_KERNEL, 0);
			if (!page)
				return -1;
			gtp_rb_page_count++;
			rb->w = GTP_RB_DATA(page_address(page));
			GTP_RB_NEXT(rb->w) = next;
			if (next)
				GTP_RB_PREV(next) = rb->w;
			next = rb->w;
			if (!last)
				last = rb->w;
		}

		GTP_RB_NEXT(last) = next;
		GTP_RB_PREV(next) = last;
		rb->r = rb->w;

		if (gtp_rb_page_count < 3)
			return -1;
	}

	return 0;
}

static void
gtp_rb_page_free(void)
{
	int	cpu;

	for_each_online_cpu(cpu) {
		struct gtp_rb_s	*rb
			= (struct gtp_rb_s *)per_cpu_ptr(gtp_rb, cpu);
		void		*need_free = NULL;
		int		is_first = 1;

		for (rb->r = rb->w = GTP_RB_DATA(rb->w);
		     is_first || rb->w != rb->r;
		     rb->w = GTP_RB_NEXT(rb->w)) {
			if (need_free)
				free_page((unsigned long)need_free);
			need_free = GTP_RB_HEAD(rb->w);
			is_first = 0;
		}
		if (need_free)
			free_page((unsigned long)need_free);
	}

	gtp_rb_page_count = 0;
}

#define GTP_RB_LOCK(r)			spin_lock(&r->lock)
#define GTP_RB_UNLOCK(r)		spin_unlock(&r->lock)
#define GTP_RB_LOCK_IRQ(r, flags)	spin_lock_irqsave(&r->lock, flags)
#define GTP_RB_UNLOCK_IRQ(r, flags)	spin_unlock_irqrestore(&r->lock, flags)
#define GTP_RB_RELEASE(r)		(r->w = r->prev_w)

static inline void *
gtp_rb_prev_frame_get(struct gtp_rb_s *rb)
{
	return rb->prev_frame;
}

static inline void
gtp_rb_prev_frame_set(struct gtp_rb_s *rb, void *prev_frame)
{
	rb->prev_frame = prev_frame;
}

static void *
gtp_rb_alloc(struct gtp_rb_s *rb, size_t size, u64 id)
{
	void		*ret;

	size = FRAME_ALIGN(size);

	if (size > GTP_RB_DATA_MAX) {
		printk(KERN_WARNING "gtp_rb_alloc: The size %zu is too big"
				    "for the KGTP ring buffer.  "
				    "The max size that KGTP ring buffer "
				    "support is %lu (Need sub some size for "
				    "inside structure).\n", size, GTP_RB_DATA_MAX);
		return NULL;
	}

	rb->prev_w = rb->w;

	if (rb->w + size > GTP_RB_END(rb->w)) {
		/* Don't have enough size in current page, insert a
		   FID_PAGE_END and try to get next page.  */
		if (GTP_RB_END(rb->w) - rb->w >= FID_SIZE)
			FID(rb->w) = FID_PAGE_END;

		if (GTP_RB_HEAD(GTP_RB_NEXT(rb->w)) == GTP_RB_HEAD(rb->r)) {
			if (gtp_circular) {
				rb->r = GTP_RB_NEXT(rb->r);
				atomic_inc(&gtp_rb_discard_page_number);
			} else
				return NULL;
		}
		rb->w = GTP_RB_NEXT(rb->w);

		if (id) {
			/* Need insert a FID_PAGE_BEGIN.  */
			FID(rb->w) = FID_PAGE_BEGIN;
			*((u64 *)(rb->w + FID_SIZE)) = id;
			rb->w += FRAME_ALIGN(GTP_FRAME_PAGE_BEGIN_SIZE);
		}
	}

	ret = rb->w;
	rb->w += size;

	return ret;
}

enum gtp_rb_walk_reason {
	gtp_rb_walk_end = 0,
	gtp_rb_walk_end_page,
	gtp_rb_walk_end_entry,
	gtp_rb_walk_new_entry,
	gtp_rb_walk_type,
	gtp_rb_walk_step,
	gtp_rb_walk_error,
};

/* Check *end.  */
#define GTP_RB_WALK_CHECK_END	0x1

/* When to the end of a page, goto next one.  */
#define GTP_RB_WALK_PASS_PAGE	0x2

/* When to the end of a entry, goto next one.
   If not set, stop in the first address of next entry and
   set S->REASON to gtp_rb_walk_new_entry.  */
#define GTP_RB_WALK_PASS_ENTRY	0x4

/* Check with id and FID_PAGE_BEGIN to make sure this is the current frame.  */
#define GTP_RB_WALK_CHECK_ID	0x8

/* Return and set S->REASON to gtp_rb_walk_type if type is same entry type.  */
#define GTP_RB_WALK_CHECK_TYPE	0x10

/* Walk STEP step in ring_buffer, just record FID_REG, FID_MEM, FID_VAR.  */
#define GTP_RB_WALK_STEP	0x20

struct gtp_rb_walk_s {
	unsigned int		flags;

	/* Reason for return.  */
	enum gtp_rb_walk_reason	reason;

	/* GTP_RB_WALK_CHECK_END,
	   it will point to the end of this ring buffer.  */
	void			*end;

	/* GTP_RB_WALK_CHECK_ID */
	u64			id;

	/* GTP_RB_WALK_CHECK_TYPE */
	FID_TYPE		type;

	/* GTP_RB_WALK_STEP */
	int			step;
};

/* Walk in ring buffer RET according to S.  And return the new pointer.  */

static void *
gtp_rb_walk(struct gtp_rb_walk_s *s, void *ret)
{
	int	step;
	void	*page_end = GTP_RB_END(ret);

	if (s->flags & GTP_RB_WALK_STEP)
		step = 0;

	while (1) {
		FID_TYPE	fid;

		if ((s->flags & GTP_RB_WALK_CHECK_END) && ret == s->end) {
			s->reason = gtp_rb_walk_end;
			break;
		}

		if (ret == page_end || page_end - ret < FID_SIZE
		    || FID(ret) == FID_PAGE_END) {
			if (!(s->flags & GTP_RB_WALK_PASS_PAGE)) {
				s->reason = gtp_rb_walk_end_page;
				break;
			}
			ret = GTP_RB_NEXT(ret);
			page_end = GTP_RB_END(ret);
			continue;
		}

		fid = FID(ret);

		if ((s->flags & GTP_RB_WALK_CHECK_TYPE) && s->type == fid) {
			s->reason = gtp_rb_walk_type;
			break;
		}

		if ((s->flags & GTP_RB_WALK_STEP)
		    && (fid == FID_REG || fid == FID_MEM || fid == FID_VAR)) {
			if (step >= s->step) {
				s->reason = gtp_rb_walk_step;
				break;
			}
			step++;
		}

		switch (fid) {
		case FID_HEAD:
			if (!(s->flags & GTP_RB_WALK_PASS_ENTRY)) {
				s->reason = gtp_rb_walk_new_entry;
				goto out;
			}
			ret += FRAME_ALIGN(GTP_FRAME_HEAD_SIZE);
			break;
		case FID_REG:
			ret += FRAME_ALIGN(GTP_FRAME_REG_SIZE);
			break;
		case FID_MEM: {
				struct gtp_frame_mem	*gfm;

				gfm = (struct gtp_frame_mem *) (ret + FID_SIZE);
				ret += FRAME_ALIGN(GTP_FRAME_MEM_SIZE
						   + gfm->size);
			}
			break;
		case FID_VAR:
			ret += FRAME_ALIGN(GTP_FRAME_VAR_SIZE);
			break;
		case FID_PAGE_BEGIN:
			if ((s->flags & GTP_RB_WALK_CHECK_ID)
			    && s->id != *(u64 *)(ret + FID_SIZE)) {
				s->reason = gtp_rb_walk_end_entry;
				goto out;
			}
			ret += FRAME_ALIGN(GTP_FRAME_PAGE_BEGIN_SIZE);
			break;
		default:
			printk(KERN_WARNING
			       "Walk in gtp ring buffer got error id 0x%x "
			       "in 0x%p.\n",
			       fid, ret);
			s->reason = gtp_rb_walk_error;
			goto out;
			break;
		}
	}

out:
	return ret;
}

static void *
gtp_rb_walk_reverse(void *buf, void *begin)
{
	if (buf == begin)
		return NULL;
	buf = *(void **)(buf + FID_SIZE + sizeof(u64) + sizeof(ULONGEST));

	return buf;
}

static struct gtp_rb_s	*gtp_frame_current_rb;
static u64		gtp_frame_current_id;
static struct pt_regs	*gtp_frame_current_regs;

static void
gtp_rb_read_reset(void)
{
	int	cpu;

	for_each_online_cpu(cpu) {
		struct gtp_rb_s	*rb
			= (struct gtp_rb_s *)per_cpu_ptr(gtp_rb, cpu);

		rb->rp = rb->r;
		rb->rp_id = 0;
	}
	gtp_frame_current_num = -1;
	gtp_frame_current_rb = NULL;
}

static void
gtp_rb_update_gtp_frame_current(void)
{
	gtp_frame_current_id = *(u64 *)(gtp_frame_current_rb->rp + FID_SIZE);
	gtp_frame_current_tpe = *(ULONGEST *)(gtp_frame_current_rb->rp
					      + FID_SIZE + sizeof(u64));
	gtp_frame_current_rb->rp += FRAME_ALIGN(GTP_FRAME_HEAD_SIZE);
	gtp_frame_current_regs = NULL;
}

static int
gtp_rb_read(void)
{
	int			cpu;
	u64			min_id = ULLONG_MAX;
	struct gtp_rb_walk_s	rbws;

	gtp_frame_current_rb = NULL;

	rbws.flags = GTP_RB_WALK_PASS_PAGE | GTP_RB_WALK_CHECK_END;

	for_each_online_cpu(cpu) {
		struct gtp_rb_s	*rb
			= (struct gtp_rb_s *)per_cpu_ptr(gtp_rb, cpu);

		if (rb->rp == NULL)
			rb->rp = rb->r;

		if (rb->rp_id == 0) {
			rbws.end = rb->w;
			rb->rp = gtp_rb_walk(&rbws, rb->rp);
			if (rbws.reason != gtp_rb_walk_new_entry)
				continue;
			rb->rp_id = *(u64 *)(rb->rp + FID_SIZE);
		}
		if (rb->rp_id < min_id) {
			min_id = rb->rp_id;
			gtp_frame_current_rb = rb;
		}
	}

	if (gtp_frame_current_rb == NULL) {
		gtp_rb_read_reset();
		return -1;
	}

	gtp_frame_current_rb->rp_id = 0;
	gtp_rb_update_gtp_frame_current();
	gtp_frame_current_num += 1;

	return 0;
}

static void *
gtp_rb_get_page(struct gtp_rb_s *rb)
{
	void		*ret = NULL;
	unsigned long	flags;

	GTP_RB_LOCK_IRQ(rb, flags);

	if (GTP_RB_HEAD(rb->r) == GTP_RB_HEAD(rb->w)) {
		if (rb->r == rb->w)
			goto out;
		/* Move rb->w to next page.  */
		if (GTP_RB_END(rb->w) - rb->w >= FID_SIZE)
			FID(rb->w) = FID_PAGE_END;
		rb->w = GTP_RB_NEXT(rb->w);
	}

	ret = rb->r;
	{
		/* Move this page out of ring.  */
		void	*prev = GTP_RB_PREV(rb->r);
		void	*next = GTP_RB_NEXT(rb->r);

		GTP_RB_NEXT(prev) = next;
		GTP_RB_PREV(next) = prev;
		rb->r = next;
	}

out:
	GTP_RB_UNLOCK_IRQ(rb, flags);
	return ret;
}

static void
gtp_rb_put_page(struct gtp_rb_s *rb, void *page, int page_is_empty)
{
	void	*prev, *next;
	unsigned long	flags;

	GTP_RB_LOCK_IRQ(rb, flags);

	if (page_is_empty) {
		page = GTP_RB_DATA(page);
		if (rb->w == GTP_RB_DATA(rb->w)) {
			/* Set page before rb->w and set it as rb->w.
			   If need, set it as rb->r.  */
			prev = GTP_RB_PREV(rb->w);
			next = rb->w;
			if (rb->r == rb->w)
				rb->r = page;
			rb->w = page;
		} else {
			/* Set page after rb->w.  */
			prev = GTP_RB_DATA(rb->w);
			next = GTP_RB_NEXT(rb->w);
		}
	} else {
		if (rb->r == GTP_RB_DATA(rb->r)) {
			/* Current rb->r page is point to the begin of a page.
			   Set page before rb->r and set it as rb->r.  */
			prev = GTP_RB_PREV(rb->r);
			next = rb->r;
		} else {
			/* Current rb->r page is not point to the begin of a
			   page, give up this data.
			   Set page after rb->r and set it as rb->r.  */
			prev = GTP_RB_DATA(rb->r);
			next = GTP_RB_NEXT(rb->r);
		}
		rb->r = page;
	}

	GTP_RB_NEXT(prev) = GTP_RB_DATA(page);
	GTP_RB_PREV(next) = GTP_RB_DATA(page);
	GTP_RB_PREV(page) = prev;
	GTP_RB_NEXT(page) = next;

	GTP_RB_UNLOCK_IRQ(rb, flags);
}
