/*
 * Get the trace frame of KGTP and save it in tfile.
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
 * Copyright(C) KGTP team (https://code.google.com/p/kgtp/), 2011
 */

#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdint.h>
#include <sys/vfs.h>
#include <signal.h>

#define GTP_FRAME_PIPE_DIR	"/sys/kernel/debug/gtpframe_pipe"

int	free_size_g = 2;
int	keep_running = 1;
int	entry_number = 1000;

/*
 Return true if current disk avaial is small than fs_avail.
 */
int
check_disk_size(void)
{
	struct statfs	info;

	if (statfs("./", &info) < 0) {
		perror("statfs");
		exit(-errno);
	}

	if (info.f_bavail * info.f_bsize / 1024 / 1024/ 1024 < free_size_g)
		return 1;

	return 0;
}

int
file_is_exist(char *name)
{
	struct stat	info;

	if (stat(name, &info) < 0)
		return 0;

	return 1;
}

static void
sig_int(int signo)
{
	int	c;

	printf("Quit?(y or n):");
	c = getchar();
	if (c == 'Y' || c == 'y' )
		keep_running = 0;
}

static void
sig_term(int signo)
{
	keep_running = 0;
}

void
print_usage(char *arg)
{
	printf("Get the trace frame of KGTP and save them in current \n"
	       "directory with tfile format.\n"
	       "Usage: %s [option]\n\n"

	       "  -g n    Set the minimum free size limit to n G.\n"
	       "          When free size of current disk is smaller than n G,\n"
	       "          %s will exit (-q) or wait some seconds (-w).\n"
	       "          The default value of it is 2 G.\n\n"

	       "  -q      Quit when current disk is smaller than\n"
	       "          minimum free size limit (-g).\n\n"

	       "  -w n    Wait n seconds when current disk is smaller\n"
	       "          than minimum free size limit (-g).\n\n"

	       "  -e n    Set the entry number of each tfile to n.\n"
	       "          The default value of it is 1000.\n\n"

	       "  -h      Display this information.\n",
	       arg, arg);

	exit(0);
}

int
main(int argc,char *argv[],char *envp[])
{
	int			c;
	int			pipe;
	int			quit_if_full = 0;
	int			wait_second = 30;
	int			rec_id = 0;
	char			frame_name[64];
	struct sigaction	act;

	while ((c = getopt(argc, argv, "g:qw:e:h")) != -1) {
		switch (c) {
		case 'g':
			free_size_g = atoi(optarg);
			if (free_size_g < 1) {
				fprintf(stderr, "The %d is too small.\n",
					free_size_g);
				exit(-1);
			}
			break;
		case 'q':
			quit_if_full = 1;
			break;
		case 'w':
			wait_second = atoi(optarg);
			if (wait_second <= 0) {
				fprintf(stderr, "The %d is too small.\n",
					wait_second);
				exit(-1);
			}
			break;
		case 'e':
			entry_number = atoi(optarg);
			if (entry_number <= 0) {
				fprintf(stderr, "The %d is too small.\n",
					wait_second);
				exit(-1);
			}
			break;
		case 'h':
		default:
			print_usage(argv[0]);
			break;
		}
	}

	for(; 1; rec_id++) {
		snprintf(frame_name, 64, "%d.gtp", rec_id);
		if (!file_is_exist(frame_name))
			break;
	}

	pipe = open(GTP_FRAME_PIPE_DIR, O_RDONLY);
	if (pipe < 0) {
		perror(GTP_FRAME_PIPE_DIR);
		exit(-errno);
	}

	act.sa_handler = sig_int;
	act.sa_flags = 0;
	if (sigaction(SIGINT, &act, NULL)< 0) {
		perror("sigaction");
		exit(-errno);
	}
	act.sa_handler = sig_term;
	act.sa_flags = 0;
	if (sigaction(SIGTERM, &act, NULL)< 0) {
		perror("sigaction");
		exit(-errno);
	}

	while (keep_running) {
		int	fd;
		char	tmp_name[] = ".gtpframe.XXXXXX";
		int	num;
		ssize_t	buf_size;
		char	buf[8192];

		/* Check size.  */
		if (check_disk_size()) {
			printf("Free disk size is smaller than %dG.\n",
			       free_size_g);
			if (quit_if_full)
				exit(0);
			else {
				printf("Wait %d seconds.\n", wait_second);
				sleep(wait_second);
				continue;
			}
		}

re_open:
		if (mkstemp(tmp_name) == -1) {
			perror("mkstemp");
			exit(-errno);
		}
		fd = open(tmp_name, O_WRONLY | O_CREAT | O_EXCL, S_IRWXU);
		if (fd < 0) {
			if (errno == EEXIST || (errno == EINTR && keep_running))
				goto re_open;
			perror(tmp_name);
			exit(-errno);
		}

		if (lseek(pipe, 0, SEEK_SET) < 0) {
			perror("lseek");
			exit(-errno);
		}

		for (num = 0; num < entry_number + 1; num++) {
re_read:
			buf_size = read(pipe, buf, 8192);
			if (buf_size <= 0) {
				if (errno == EINTR) {
					if (keep_running)
						goto re_read;
					else
						break;
				}
				perror(GTP_FRAME_PIPE_DIR);
				exit(-errno);
			}
re_write:
			if (write(fd, buf, buf_size) != buf_size) {
				if (errno == EINTR)
					goto re_write;
				perror("write");
				if (num > 0)
					break;
				exit(-errno);
			}
		}

		memset(buf, 0, 2);
re_write_2:
		if (write(fd, buf, 2) != 2) {
			if (errno == EINTR)
				goto re_write_2;
			perror("Write tail");
		}
		close(fd);

		if (num < 2)
			unlink(tmp_name);
		else {
			for(; 1; rec_id++) {
				snprintf(frame_name, 64, "%d.gtp", rec_id);
				if (!file_is_exist(frame_name))
					break;
			}
			if (rename(tmp_name, frame_name) < 0) {
				perror("rename");
				exit(-errno);
			}
			printf("Save KGTP trace frame buffer to file %s.\n",
			       frame_name);
		}
	}

	return 0;
}
