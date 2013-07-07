/*
 * Following part is base on kernel/events/core.c
 * commit 9985c20f9e4aee6857c08246b273a3695a52b929
 * Following part is base on kernel/events/internal.h
 * commit a8b0ca17b80e92faab46ee7179ba9e99ccb61233
 * Following part is base on kernel/events/ring_buffer.c
 * commit a7ac67ea021b4603095d2aa458bc41641238f22c
 */

#if (LINUX_VERSION_CODE < KERNEL_VERSION(3,3,0))

#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3,1,0)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,4))
struct ring_buffer {
	atomic_t			refcount;
	struct rcu_head			rcu_head;
#ifdef CONFIG_PERF_USE_VMALLOC
	struct work_struct		work;
	int				page_order;	/* allocation order  */
#endif
	int				nr_pages;	/* nr of data pages  */
	int				writable;	/* are we writable   */

	atomic_t			poll;		/* POLL_ for wakeups */

	local_t				head;		/* write position    */
	local_t				nest;		/* nested writers    */
	local_t				events;		/* event limit       */
	local_t				wakeup;		/* wakeup stamp      */
	local_t				lost;		/* nr records lost   */

	long				watermark;	/* wakeup watermark  */

	struct perf_event_mmap_page	*user_page;
	void				*data_pages[0];
};
#endif

static inline u64 perf_clock(void)
{
	return GTP_LOCAL_CLOCK;
}

#if (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,36)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,1))
static inline struct perf_cpu_context *
__get_cpu_context(struct perf_event_context *ctx)
{
	return this_cpu_ptr(ctx->pmu->pmu_cpu_context);
}
#else
static DEFINE_PER_CPU(struct perf_cpu_context, perf_cpu_context);
#endif

/* KGTP doesn't support PERF_FLAG_PID_CGROUP */
static inline int is_cgroup_event(struct perf_event *event)
{
	return 0;
}

/* KGTP doesn't support PERF_FLAG_PID_CGROUP */
static inline bool
perf_cgroup_match(struct perf_event *event)
{
	return true;
}

/*
 * Update the record of the current time in a context.
 */
static void update_context_time(struct perf_event_context *ctx)
{
	u64 now = perf_clock();

	ctx->time += now - ctx->timestamp;
	ctx->timestamp = now;
}

static u64 perf_event_time(struct perf_event *event)
{
	struct perf_event_context *ctx = event->ctx;

	/* KGTP doesn't support PERF_FLAG_PID_CGROUP */
	/*
	if (is_cgroup_event(event))
		return perf_cgroup_event_time(event);
	*/

	return ctx ? ctx->time : 0;
}

/*
 * Update the total_time_enabled and total_time_running fields for a event.
 */
static void update_event_times(struct perf_event *event)
{
	struct perf_event_context *ctx = event->ctx;
	u64 run_end;

	if (event->state < PERF_EVENT_STATE_INACTIVE ||
	    event->group_leader->state < PERF_EVENT_STATE_INACTIVE)
		return;
	/*
	 * in cgroup mode, time_enabled represents
	 * the time the event was enabled AND active
	 * tasks were in the monitored cgroup. This is
	 * independent of the activity of the context as
	 * there may be a mix of cgroup and non-cgroup events.
	 *
	 * That is why we treat cgroup events differently
	 * here.
	 */
	if (is_cgroup_event(event))
		run_end = perf_event_time(event);
	else if (ctx->is_active)
		run_end = ctx->time;
	else
		run_end = event->tstamp_stopped;

	event->total_time_enabled = run_end - event->tstamp_enabled;

	if (event->state == PERF_EVENT_STATE_INACTIVE)
		run_end = event->tstamp_stopped;
	else
		run_end = perf_event_time(event);

	event->total_time_running = run_end - event->tstamp_running;

}

static inline int
event_filter_match(struct perf_event *event)
{
	return (event->cpu == -1 || event->cpu == smp_processor_id())
	    && perf_cgroup_match(event);
}

static void
event_sched_out(struct perf_event *event,
		  struct perf_cpu_context *cpuctx,
		  struct perf_event_context *ctx)
{
	u64 tstamp = perf_event_time(event);
	u64 delta;
	/*
	 * An event which could not be activated because of
	 * filter mismatch still needs to have its timings
	 * maintained, otherwise bogus information is return
	 * via read() for time_enabled, time_running:
	 */
	if (event->state == PERF_EVENT_STATE_INACTIVE
	    && !event_filter_match(event)) {
		delta = tstamp - event->tstamp_stopped;
		event->tstamp_running += delta;
		event->tstamp_stopped = tstamp;
	}

	if (event->state != PERF_EVENT_STATE_ACTIVE)
		return;

	event->state = PERF_EVENT_STATE_INACTIVE;
	if (event->pending_disable) {
		event->pending_disable = 0;
		event->state = PERF_EVENT_STATE_OFF;
	}
	event->tstamp_stopped = tstamp;
#if (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,36)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,1))
	event->pmu->del(event, 0);
#else
	event->pmu->disable(event);
#endif
	event->oncpu = -1;

	if (!is_software_event(event))
		cpuctx->active_oncpu--;
	ctx->nr_active--;
	if (event->attr.exclusive || !cpuctx->active_oncpu)
		cpuctx->exclusive = 0;
}

/*
 * Put a event into inactive state and update time fields.
 * Enabling the leader of a group effectively enables all
 * the group members that aren't explicitly disabled, so we
 * have to update their ->tstamp_enabled also.
 * Note: this works for group members as well as group leaders
 * since the non-leader members' sibling_lists will be empty.
 */
static void __perf_event_mark_enabled(struct perf_event *event,
					struct perf_event_context *ctx)
{
	struct perf_event *sub;
	u64 tstamp = perf_event_time(event);

	event->state = PERF_EVENT_STATE_INACTIVE;
	event->tstamp_enabled = tstamp - event->total_time_enabled;
	list_for_each_entry(sub, &event->sibling_list, group_entry) {
		if (sub->state >= PERF_EVENT_STATE_INACTIVE)
			sub->tstamp_enabled = tstamp - sub->total_time_enabled;
	}
}

#if (LINUX_VERSION_CODE < KERNEL_VERSION(2,6,34)) \
    && (RHEL_RELEASE_CODE < RHEL_RELEASE_VERSION(6,1))
/*
 * Return 1 for a group consisting entirely of software events,
 * 0 if the group contains any hardware events.
 */
static int is_software_only_group(struct perf_event *leader)
{
	struct perf_event *event;

	if (!is_software_event(leader))
		return 0;

	list_for_each_entry(event, &leader->sibling_list, group_entry)
		if (!is_software_event(event))
			return 0;

	return 1;
}
#endif

/*
 * Work out whether we can put this event group on the CPU now.
 */
static int group_can_go_on(struct perf_event *event,
			   struct perf_cpu_context *cpuctx,
			   int can_add_hw)
{
#if (LINUX_VERSION_CODE < KERNEL_VERSION(2,6,34)) \
    && (RHEL_RELEASE_CODE < RHEL_RELEASE_VERSION(6,1))
	/*
	 * Groups consisting entirely of software events can always go on.
	 */
	if (is_software_only_group(event))
		return 1;
#else
	/*
	 * Groups consisting entirely of software events can always go on.
	 */
	if (event->group_flags & PERF_GROUP_SOFTWARE)
		return 1;
#endif

	/*
	 * If an exclusive group is already on, no other hardware
	 * events can go on.
	 */
	if (cpuctx->exclusive)
		return 0;
	/*
	 * If this group is exclusive and there are already
	 * events on the CPU, it can't go on.
	 */
	if (event->attr.exclusive && cpuctx->active_oncpu)
		return 0;
	/*
	 * Otherwise, try to add it if all previous groups were able
	 * to go on.
	 */
	return can_add_hw;
}

#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3,1,0)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,4))
#ifndef CONFIG_PERF_USE_VMALLOC
static inline int page_order(struct ring_buffer *rb)
{
	return 0;
}
#else
/*
 * Back perf_mmap() with vmalloc memory.
 *
 * Required for architectures that have d-cache aliasing issues.
 */

static inline int page_order(struct ring_buffer *rb)
{
	return rb->page_order;
}
#endif
#else
#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,36)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,1))
#ifndef CONFIG_PERF_USE_VMALLOC
static inline int page_order(struct perf_buffer *buffer)
{
	return 0;
}
#else
static inline int page_order(struct perf_buffer *buffer)
{
	return buffer->page_order;
}
#endif
#else
#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,35))
#ifndef CONFIG_PERF_USE_VMALLOC
static inline int page_order(struct perf_mmap_data *data)
{
	return 0;
}
#else
static inline int page_order(struct perf_mmap_data *data)
{
	return data->page_order;
}
#endif
#else
static inline int page_order(struct perf_mmap_data *data)
{
	return data->data_order;
}
#endif
#endif
#endif

#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,35)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,1))
__always_inline void perf_output_copy(struct perf_output_handle *handle,
		      const void *buf, unsigned int len)
{
	do {
		unsigned long size = min_t(unsigned long, handle->size, len);

		memcpy(handle->addr, buf, size);

		len -= size;
		handle->addr += size;
		buf += size;
		handle->size -= size;
		if (!handle->size) {
#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3,1,0)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,4))
			struct ring_buffer *buffer = handle->rb;
#elif (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,35)) \
      || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,1))
			struct perf_buffer *buffer = handle->buffer;
#else
			struct perf_mmap_data *buffer = handle->data;
#endif

			handle->page++;
			handle->page &= buffer->nr_pages - 1;
			handle->addr = buffer->data_pages[handle->page];
			handle->size = PAGE_SIZE << page_order(buffer);
		}
	} while (len);
}
#else
void perf_output_copy(struct perf_output_handle *handle,
		      const void *buf, unsigned int len)
{
	unsigned int pages_mask;
	unsigned long offset;
	unsigned int size;
	void **pages;

	offset		= handle->offset;
	pages_mask	= handle->data->nr_pages - 1;
	pages		= handle->data->data_pages;

	do {
		unsigned long page_offset;
		unsigned long page_size;
		int nr;

		nr	    = (offset >> PAGE_SHIFT) & pages_mask;
		page_size   = 1UL << (handle->data->data_order + PAGE_SHIFT);
		page_offset = offset & (page_size - 1);
		size	    = min_t(unsigned int, page_size - page_offset, len);

		memcpy(pages[nr] + page_offset, buf, size);

		len	    -= size;
		buf	    += size;
		offset	    += size;
	} while (len);

	handle->offset = offset;

	/*
	 * Check we didn't copy past our reservation window, taking the
	 * possible unsigned int wrap into account.
	 */
	WARN_ON_ONCE(((long)(handle->head - handle->offset)) < 0);
}
#endif

#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,38))

/*
 * If we inherit events we want to return the parent event id
 * to userspace.
 */
static u64 primary_event_id(struct perf_event *event)
{
	u64 id = event->id;

	if (event->parent)
		id = event->parent->id;

	return id;
}

static u32 perf_event_pid(struct perf_event *event, struct task_struct *p)
{
	/*
	 * only top level events have the pid namespace they were created in
	 */
	if (event->parent)
		event = event->parent;

	return task_tgid_nr_ns(p, event->ns);
}

static u32 perf_event_tid(struct perf_event *event, struct task_struct *p)
{
	/*
	 * only top level events have the pid namespace they were created in
	 */
	if (event->parent)
		event = event->parent;

	return task_pid_nr_ns(p, event->ns);
}

static void __perf_event_header__init_id(struct perf_event_header *header,
					 struct perf_sample_data *data,
					 struct perf_event *event)
{
	u64 sample_type = event->attr.sample_type;

	data->type = sample_type;
	header->size += event->id_header_size;

	if (sample_type & PERF_SAMPLE_TID) {
		/* namespace issues */
		data->tid_entry.pid = perf_event_pid(event, current);
		data->tid_entry.tid = perf_event_tid(event, current);
	}

	if (sample_type & PERF_SAMPLE_TIME)
		data->time = perf_clock();

	if (sample_type & PERF_SAMPLE_ID)
		data->id = primary_event_id(event);

	if (sample_type & PERF_SAMPLE_STREAM_ID)
		data->stream_id = event->id;

	if (sample_type & PERF_SAMPLE_CPU) {
		data->cpu_entry.cpu	 = raw_smp_processor_id();
		data->cpu_entry.reserved = 0;
	}
}

static void __perf_event__output_id_sample(struct perf_output_handle *handle,
					   struct perf_sample_data *data)
{
	u64 sample_type = data->type;

	if (sample_type & PERF_SAMPLE_TID)
		perf_output_put(handle, data->tid_entry);

	if (sample_type & PERF_SAMPLE_TIME)
		perf_output_put(handle, data->time);

	if (sample_type & PERF_SAMPLE_ID)
		perf_output_put(handle, data->id);

	if (sample_type & PERF_SAMPLE_STREAM_ID)
		perf_output_put(handle, data->stream_id);

	if (sample_type & PERF_SAMPLE_CPU)
		perf_output_put(handle, data->cpu_entry);
}

static void perf_event_header__init_id(struct perf_event_header *header,
				       struct perf_sample_data *data,
				       struct perf_event *event)
{
	if (event->attr.sample_id_all)
		__perf_event_header__init_id(header, data, event);
}

static void perf_event__output_id_sample(struct perf_event *event,
					 struct perf_output_handle *handle,
					 struct perf_sample_data *sample)
{
	if (event->attr.sample_id_all)
		__perf_event__output_id_sample(handle, sample);
}

#if (LINUX_VERSION_CODE < KERNEL_VERSION(3,1,0)) \
    && (RHEL_RELEASE_CODE < RHEL_RELEASE_VERSION(6,4))
static void gtp_perf_event_wakeup(struct perf_event *event)
{
	wake_up_all(&event->waitq);

	if (event->pending_kill) {
		kill_fasync(&event->fasync, SIGIO, event->pending_kill);
		event->pending_kill = 0;
	}
}
#endif

static void perf_output_wakeup(struct perf_output_handle *handle)
{
#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3,1,0)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,4))
	atomic_set(&handle->rb->poll, POLL_IN);
#else
	atomic_set(&handle->buffer->poll, POLL_IN);
#endif

#if (LINUX_VERSION_CODE < KERNEL_VERSION(3,1,0)) \
    && (RHEL_RELEASE_CODE < RHEL_RELEASE_VERSION(6,4))
	if (handle->nmi) {
#endif
		handle->event->pending_wakeup = 1;
		irq_work_queue(&handle->event->pending);
#if (LINUX_VERSION_CODE < KERNEL_VERSION(3,1,0)) \
    && (RHEL_RELEASE_CODE < RHEL_RELEASE_VERSION(6,4))
	} else
		gtp_perf_event_wakeup(handle->event);
#endif
}

static void perf_output_put_handle(struct perf_output_handle *handle)
{
#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3,1,0)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,4))
	struct ring_buffer *buffer = handle->rb;
#else
	struct perf_buffer *buffer = handle->buffer;
#endif
	unsigned long head;

again:
	head = local_read(&buffer->head);

	/*
	 * IRQ/NMI can happen here, which means we can miss a head update.
	 */

	if (!local_dec_and_test(&buffer->nest))
		goto out;

	/*
	 * Publish the known good head. Rely on the full barrier implied
	 * by atomic_dec_and_test() order the buffer->head read and this
	 * write.
	 */
	buffer->user_page->data_head = head;

	/*
	 * Now check if we missed an update, rely on the (compiler)
	 * barrier in atomic_dec_and_test() to re-read buffer->head.
	 */
	if (unlikely(head != local_read(&buffer->head))) {
		local_inc(&buffer->nest);
		goto again;
	}

	if (handle->wakeup != local_read(&buffer->wakeup))
		perf_output_wakeup(handle);

out:
	preempt_enable();
}

static void gtp_perf_output_end(struct perf_output_handle *handle)
{
#if (LINUX_VERSION_CODE < KERNEL_VERSION(3,1,0)) \
    && (RHEL_RELEASE_CODE < RHEL_RELEASE_VERSION(6,4))
	struct perf_event *event = handle->event;
	struct perf_buffer *buffer = handle->buffer;

	int wakeup_events = event->attr.wakeup_events;

	if (handle->sample && wakeup_events) {
		int events = local_inc_return(&buffer->events);
		if (events >= wakeup_events) {
			local_sub(wakeup_events, &buffer->events);
			local_inc(&buffer->wakeup);
		}
	}
#endif

	perf_output_put_handle(handle);
	rcu_read_unlock();
}

#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3,1,0)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,4))
static unsigned long perf_data_size(struct ring_buffer *buffer)
#else
static unsigned long perf_data_size(struct perf_buffer *buffer)
#endif
{
	return buffer->nr_pages << (PAGE_SHIFT + page_order(buffer));
}

/*
 * Output
 */
#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3,1,0)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,4))
static bool perf_output_space(struct ring_buffer *buffer, unsigned long tail,
			      unsigned long offset, unsigned long head)
#else
static bool perf_output_space(struct perf_buffer *buffer, unsigned long tail,
			      unsigned long offset, unsigned long head)
#endif
{
	unsigned long mask;

	if (!buffer->writable)
		return true;

	mask = perf_data_size(buffer) - 1;

	offset = (offset - tail) & mask;
	head   = (head   - tail) & mask;

	if ((int)(head - offset) < 0)
		return false;

	return true;
}

/*
 * We need to ensure a later event_id doesn't publish a head when a former
 * event isn't done writing. However since we need to deal with NMIs we
 * cannot fully serialize things.
 *
 * We only publish the head (and generate a wakeup) when the outer-most
 * event completes.
 */
static void perf_output_get_handle(struct perf_output_handle *handle)
{
#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3,1,0)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,4))
	struct ring_buffer *buffer = handle->rb;
#else
	struct perf_buffer *buffer = handle->buffer;
#endif

	preempt_disable();
	local_inc(&buffer->nest);
	handle->wakeup = local_read(&buffer->wakeup);
}

static int gtp_perf_output_begin(struct perf_output_handle *handle,
				 struct perf_event *event, unsigned int size,
				 int nmi, int sample)
{
#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3,1,0)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,4))
	struct ring_buffer *buffer;
#else
	struct perf_buffer *buffer;
#endif
	unsigned long tail, offset, head;
	int have_lost;
	struct perf_sample_data sample_data;
	struct {
		struct perf_event_header header;
		u64			 id;
		u64			 lost;
	} lost_event;

	rcu_read_lock();
	/*
	 * For inherited events we send all the output towards the parent.
	 */
	if (event->parent)
		event = event->parent;

#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3,1,0)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,4))
	buffer = rcu_dereference(event->rb);
#else
	buffer = rcu_dereference(event->buffer);
#endif
	if (!buffer)
		goto out;

#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3,1,0)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,4))
	handle->rb	= buffer;
#else
	handle->buffer	= buffer;
#endif
	handle->event	= event;
#if (LINUX_VERSION_CODE < KERNEL_VERSION(3,1,0)) \
    && (RHEL_RELEASE_CODE < RHEL_RELEASE_VERSION(6,4))
	handle->nmi	= nmi;
	handle->sample	= sample;
#endif

	if (!buffer->nr_pages)
		goto out;

	have_lost = local_read(&buffer->lost);
	if (have_lost) {
		lost_event.header.size = sizeof(lost_event);
		perf_event_header__init_id(&lost_event.header, &sample_data,
					   event);
		size += lost_event.header.size;
	}

	perf_output_get_handle(handle);

	do {
		/*
		 * Userspace could choose to issue a mb() before updating the
		 * tail pointer. So that all reads will be completed before the
		 * write is issued.
		 */
		tail = ACCESS_ONCE(buffer->user_page->data_tail);
		smp_rmb();
		offset = head = local_read(&buffer->head);
		head += size;
		if (unlikely(!perf_output_space(buffer, tail, offset, head)))
			goto fail;
	} while (local_cmpxchg(&buffer->head, offset, head) != offset);

	if (head - local_read(&buffer->wakeup) > buffer->watermark)
		local_add(buffer->watermark, &buffer->wakeup);

	handle->page = offset >> (PAGE_SHIFT + page_order(buffer));
	handle->page &= buffer->nr_pages - 1;
	handle->size = offset & ((PAGE_SIZE << page_order(buffer)) - 1);
	handle->addr = buffer->data_pages[handle->page];
	handle->addr += handle->size;
	handle->size = (PAGE_SIZE << page_order(buffer)) - handle->size;

	if (have_lost) {
		lost_event.header.type = PERF_RECORD_LOST;
		lost_event.header.misc = 0;
		lost_event.id          = event->id;
		lost_event.lost        = local_xchg(&buffer->lost, 0);

		perf_output_put(handle, lost_event);
		perf_event__output_id_sample(event, handle, &sample_data);
	}

	return 0;

fail:
	local_inc(&buffer->lost);
	perf_output_put_handle(handle);
out:
	rcu_read_unlock();

	return -ENOSPC;
}

/*
 * IRQ throttle logging
 */

static void perf_log_throttle(struct perf_event *event, int enable)
{
	struct perf_output_handle handle;
	struct perf_sample_data sample;
	int ret;

	struct {
		struct perf_event_header	header;
		u64				time;
		u64				id;
		u64				stream_id;
	} throttle_event = {
		.header = {
			.type = PERF_RECORD_THROTTLE,
			.misc = 0,
			.size = sizeof(throttle_event),
		},
		.time		= perf_clock(),
		.id		= primary_event_id(event),
		.stream_id	= event->id,
	};

	if (enable)
		throttle_event.header.type = PERF_RECORD_UNTHROTTLE;

	perf_event_header__init_id(&throttle_event.header, &sample, event);

	ret = gtp_perf_output_begin(&handle, event,
				    throttle_event.header.size, 1, 0);
	if (ret)
		return;

	perf_output_put(&handle, throttle_event);
	perf_event__output_id_sample(event, &handle, &sample);
	gtp_perf_output_end(&handle);
}
#endif

static void perf_set_shadow_time(struct perf_event *event,
				 struct perf_event_context *ctx,
				 u64 tstamp)
{
	/*
	 * use the correct time source for the time snapshot
	 *
	 * We could get by without this by leveraging the
	 * fact that to get to this function, the caller
	 * has most likely already called update_context_time()
	 * and update_cgrp_time_xx() and thus both timestamp
	 * are identical (or very close). Given that tstamp is,
	 * already adjusted for cgroup, we could say that:
	 *    tstamp - ctx->timestamp
	 * is equivalent to
	 *    tstamp - cgrp->timestamp.
	 *
	 * Then, in perf_output_read(), the calculation would
	 * work with no changes because:
	 * - event is guaranteed scheduled in
	 * - no scheduled out in between
	 * - thus the timestamp would be the same
	 *
	 * But this is a bit hairy.
	 *
	 * So instead, we have an explicit cgroup call to remain
	 * within the time time source all along. We believe it
	 * is cleaner and simpler to understand.
	 */
	/* KGTP doesn't support PERF_FLAG_PID_CGROUP */
#if 0
	if (is_cgroup_event(event))
		perf_cgroup_set_shadow_time(event, tstamp);
	else
#endif
#if (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,36)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,1))
	event->shadow_ctx_time = tstamp - ctx->timestamp;
#endif
}

#define MAX_INTERRUPTS (~0ULL)

static int
event_sched_in(struct perf_event *event,
		 struct perf_cpu_context *cpuctx,
		 struct perf_event_context *ctx)
{
	u64 tstamp = perf_event_time(event);

	if (event->state <= PERF_EVENT_STATE_OFF)
		return 0;

	event->state = PERF_EVENT_STATE_ACTIVE;
	event->oncpu = smp_processor_id();

#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,38))
	/*
	 * Unthrottle events, since we scheduled we might have missed several
	 * ticks already, also for a heavily scheduling task there is little
	 * guarantee it'll get a tick in a timely manner.
	 */
	if (unlikely(event->hw.interrupts == MAX_INTERRUPTS)) {
		perf_log_throttle(event, 1);
		event->hw.interrupts = 0;
	}
#endif

	/*
	 * The new state must be visible before we turn it on in the hardware:
	 */
	smp_wmb();

#if (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,36)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,1))
	if (event->pmu->add(event, PERF_EF_START)) {
#else
	if (event->pmu->enable(event)) {
#endif
		event->state = PERF_EVENT_STATE_INACTIVE;
		event->oncpu = -1;
		return -EAGAIN;
	}

	event->tstamp_running += tstamp - event->tstamp_stopped;

	perf_set_shadow_time(event, ctx, tstamp);

	if (!is_software_event(event))
		cpuctx->active_oncpu++;
	ctx->nr_active++;

	if (event->attr.exclusive)
		cpuctx->exclusive = 1;

	return 0;
}

/*
 * Cross CPU call to enable a performance event
 */
static int __gtp_perf_event_enable(void *info)
{
	struct perf_event *event = info;
	struct perf_event_context *ctx = event->ctx;
	struct perf_event *leader = event->group_leader;
#if (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,36)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,1))
	struct perf_cpu_context *cpuctx = __get_cpu_context(ctx);
#else
	struct perf_cpu_context *cpuctx = &__get_cpu_var(perf_cpu_context);
#endif
	int err;

	if (WARN_ON_ONCE(!ctx->is_active))
		return -EINVAL;

#if (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,32))
	raw_spin_lock(&ctx->lock);
#else
	spin_lock(&ctx->lock);
#endif
#if (LINUX_VERSION_CODE < KERNEL_VERSION(3,0,0))
	ctx->is_active = 1;
#endif
	update_context_time(ctx);

	if (event->state >= PERF_EVENT_STATE_INACTIVE)
		goto unlock;

	/* KGTP doesn't support PERF_FLAG_PID_CGROUP */
	/*
	 * set current task's cgroup time reference point
	 */
	/* perf_cgroup_set_timestamp(current, ctx); */

	__perf_event_mark_enabled(event, ctx);

	if (!event_filter_match(event)) {
		/* KGTP doesn't support PERF_FLAG_PID_CGROUP */
		/*
		if (is_cgroup_event(event))
			perf_cgroup_defer_enabled(event);
		*/
		goto unlock;
	}

	/*
	 * If the event is in a group and isn't the group leader,
	 * then don't put it on unless the group is on.
	 */
	if (leader != event && leader->state != PERF_EVENT_STATE_ACTIVE)
		goto unlock;

	if (!group_can_go_on(event, cpuctx, 1)) {
		err = -EEXIST;
	} else {
		/* KGTP doesn't support PERF_FLAG_PID_CGROUP */
		/*
		if (event == leader)
			err = group_sched_in(event, cpuctx, ctx);
		else
		*/
		err = event_sched_in(event, cpuctx, ctx);
	}

	/* KGTP doesn't support group.  */
#if 0
	if (err) {
		/*
		 * If this event can't go on and it's part of a
		 * group, then the whole group has to come off.
		 */
		if (leader != event)
			group_sched_out(leader, cpuctx, ctx);
		if (leader->attr.pinned) {
			update_group_times(leader);
			leader->state = PERF_EVENT_STATE_ERROR;
		}
	}
#endif

unlock:
#if (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,32))
	raw_spin_unlock(&ctx->lock);
#else
	spin_unlock(&ctx->lock);
#endif

	return 0;
}

/*
 * Cross CPU call to disable a performance event
 */
static int __gtp_perf_event_disable(void *info)
{
	struct perf_event *event = info;
	struct perf_event_context *ctx = event->ctx;
#if (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,36)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,1))
	struct perf_cpu_context *cpuctx = __get_cpu_context(ctx);
#else
	struct perf_cpu_context *cpuctx = &__get_cpu_var(perf_cpu_context);
#endif

	/*
	 * If this is a per-task event, need to check whether this
	 * event's task is the current task on this cpu.
	 *
	 * Can trigger due to concurrent perf_event_context_sched_out()
	 * flipping contexts around.
	 */
	if (ctx->task && cpuctx->task_ctx != ctx)
		return -EINVAL;

#if (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,32))
	raw_spin_lock(&ctx->lock);
#else
	spin_lock(&ctx->lock);
#endif

	/*
	 * If the event is on, turn it off.
	 * If it is in error state, leave it in error state.
	 */
	if (event->state >= PERF_EVENT_STATE_INACTIVE) {
		update_context_time(ctx);
		/* KGTP doesn't support PERF_FLAG_PID_CGROUP */
		/* update_cgrp_time_from_event(event); */
		update_event_times(event);
		/* KGTP doesn't support group.  */
		/*
		update_group_times(event);
		if (event == event->group_leader)
			group_sched_out(event, cpuctx, ctx);
		else
		*/
		event_sched_out(event, cpuctx, ctx);
		event->state = PERF_EVENT_STATE_OFF;
	}

#if (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,32))
	raw_spin_unlock(&ctx->lock);
#else
	spin_unlock(&ctx->lock);
#endif

	return 0;
}

/**
 * cpu_function_call - call a function on the cpu
 * @func:	the function to be called
 * @info:	the function call argument
 *
 * Calls the function @func on the remote cpu.
 *
 * returns: @func return value or -ENXIO when the cpu is offline
 */
struct remote_function_call {
	struct task_struct	*p;
	int			(*func)(void *info);
	void			*info;
	int			ret;
};

static void remote_function(void *data)
{
	struct remote_function_call *tfc = data;

#if 0
	struct task_struct *p = tfc->p;

	if (p) {
		tfc->ret = -EAGAIN;
		if (task_cpu(p) != smp_processor_id() || !task_curr(p))
			return;
	}
#endif

	tfc->ret = tfc->func(tfc->info);
}

static int cpu_function_call(int cpu, int (*func) (void *info), void *info)
{
	struct remote_function_call data = {
		.p	= NULL,
		.func	= func,
		.info	= info,
		.ret	= -ENXIO, /* No such CPU */
	};

	smp_call_function_single(cpu, remote_function, &data, 1);

	return data.ret;
}

static int
gtp_perf_event_enable(struct perf_event *event)
{
	if (event->cpu == smp_processor_id())
		return __gtp_perf_event_enable(event);
	else
		return cpu_function_call(event->cpu,
					  __gtp_perf_event_enable, event);
}

static int
gtp_perf_event_disable(struct perf_event *event)
{
	if (event->cpu == smp_processor_id())
		return __gtp_perf_event_disable(event);
	else
		return cpu_function_call(event->cpu,
					 __gtp_perf_event_disable, event);
}

#endif

/*
 This function get from perf_event_reset.
 */

static void gtp_perf_event_set(struct perf_event *event, u64 val)
{
	u64	enabled, running;

	/* (void)perf_event_read(event); */
	perf_event_read_value(event, &enabled, &running);
#if (LINUX_VERSION_CODE > KERNEL_VERSION(2,6,35)) \
    || (RHEL_RELEASE_CODE >= RHEL_RELEASE_VERSION(6,1))
	local64_set(&event->count, val);
#else
	atomic64_set(&event->count, val);
#endif
	/*XXX: it need be handle later.  */
	/* perf_event_update_userpage(event); */
}
