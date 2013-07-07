/*
 * Output Linux Kernel modules info in GDB add-symbol-file format.
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
#include <sys/utsname.h>
#include <dirent.h>

#define MOD_DIR		"/lib/modules"
#define PROC_MOD	"/proc/modules"
#define SYS_MOD		"/sys/module"

#define SDIR_MAX	16

int	sdir_number = 0;
char	*sdir[SDIR_MAX];

int	rdir_number = 0;
int	rdir_current = 0;
char	*rdir[SDIR_MAX];

char	got_dir[512];

int	no_search_mod = 0;

int
search_mod_1(char *dir, char *file)
{
	DIR		*dp;
	struct dirent	*ptr;
	int		ret = 0;

	dp = opendir(dir);
	if (!dp) {
		fprintf(stderr, "#Cannot open %s: %s.\n", dir,
			strerror(errno));
		ret = -1;
		goto out;
	}
	while((ptr = readdir(dp)) != NULL) {
		char	cdir[512];

		if (ptr->d_type == DT_DIR) {
			if (strcmp(ptr->d_name, ".") == 0)
				continue;
			if (strcmp(ptr->d_name, "..") == 0)
				continue;
			snprintf(cdir, 512, "%s/%s", dir, ptr->d_name);
			if (search_mod_1(cdir, file)) {
				ret = 1;
				break;
			}
		}
		else {
			int	i;

			snprintf(cdir, 512, "%s", ptr->d_name);
			for (i = 0; i < strlen(cdir); i++) {
				if (cdir[i] == '_')
					cdir[i] = '-';
			}
			if (strcmp(cdir, file) == 0) {
				snprintf(got_dir, 512, "%s/%s", dir,
					 ptr->d_name);
				ret = 1;
				break;
			}
		}
	}
	closedir(dp);

out:
	return ret;
}

int
search_mod(char *dir, char *file)
{
	int	ret;
	char	tmp_dir[512];

	ret = search_mod_1(dir, file);
	if (ret <= 0)
		return ret;

	if (rdir_number == 0)
		return 1;

	if (rdir_current >= rdir_number)
		rdir_current--;

	strcpy(tmp_dir, got_dir);
	snprintf(got_dir, 512, "%s%s", rdir[rdir_current],
		 tmp_dir + strlen(dir));

	rdir_current++;
	return 1;
}

void
print_mod(char *name, char *addr)
{
	int		i;
	char		mod_dir[256];
	struct stat	sbuf;
	char		file[64];
	DIR		*dp;
	struct dirent	*ptr;

	snprintf(file, 64, "%s.ko", name);

	if (no_search_mod)
		printf("add-symbol-file %s %s", file, addr);
	else {
		for (i = 0; i < strlen(file); i++) {
			if (file[i] == '_')
				file[i] = '-';
		}
		for (i = 0; i < sdir_number; i++) {
			int	ret;

			if (sdir[i] == NULL)
				continue;
			ret = search_mod(sdir[i], file);
			if (ret < 0)
				sdir[i] = NULL;
			if (ret > 0)
				break;
		}
		if (i >= sdir_number) {
			for (i = 0; i < sdir_number; i++) {
				if (sdir[i])
					break;
			}
			if (i >= sdir_number) {
				no_search_mod = 1;
				fprintf(stderr, "#Cannot open any module search "
					        "directories.  Auto open -n.\n");
			} else
				fprintf(stderr, "#Cannot find file %s in the module search "
					        "directories.  Just output the command with filename.\n",
					file);
			printf("#add-symbol-file %s %s", file, addr);
		} else
			printf("add-symbol-file %s %s", got_dir, addr);
	}

	snprintf(mod_dir, 256, "%s/%s/sections", SYS_MOD, name);
	/* Check mod_dir.  */
	if (stat(mod_dir, &sbuf) || !S_ISDIR(sbuf.st_mode)) {
		fprintf(stderr, "%s is not a right directory.\n", mod_dir);
		exit(-1);
	}

	dp = opendir(mod_dir);
	if (!dp) {
		fprintf(stderr, "Cannot open %s: %s.\n", mod_dir,
			strerror(errno));
		exit(-errno);
	}
	while((ptr = readdir(dp)) != NULL) {
		if (ptr->d_type == DT_REG) {
			char	section_file_name[512];
			FILE	*fp;
			char	line[256];
			size_t	size;

			if (strcmp(ptr->d_name, ".text") == 0
			    || strcmp(ptr->d_name, ".symtab") == 0
			    || strcmp(ptr->d_name, ".strtab") == 0)
				continue;

			snprintf(section_file_name, 512, "%s/%s", mod_dir,
				 ptr->d_name);
			fp = fopen(section_file_name, "r");
			if (!fp) {
				perror(section_file_name);
				exit(-errno);
			}
			if (fgets(line, 256, fp) == NULL) {
				perror(section_file_name);
				exit(-errno);
			}
			fclose(fp);
			size = strlen(line);
			if (size == 0) {
				fprintf(stderr, "format of %s is not right.\n",
					section_file_name);
				exit(-errno);
			}
			if (line[size - 1] == '\n')
				line[size - 1] = '\0';
			printf(" -s %s %s", ptr->d_name, line);
		}
	}
	closedir(dp);

	printf ("\n");
}

int
check_sdir(char *dir)
{
	struct stat	sbuf;

	if (stat(dir, &sbuf) || !S_ISDIR(sbuf.st_mode)) {
		fprintf(stderr, "#%s is not a right directory.  Ignore it.\n", dir);
		return 0;
	}

	return 1;
}

void
add_sdir(char *dir)
{
	if (sdir_number < SDIR_MAX) {
		if (check_sdir(dir)) {
			sdir[sdir_number] = dir;
			sdir_number++;
		}
	}
	else {
		fprintf(stderr, "Set too much module search directory.");
		exit(-1);
	}
}

void
add_rdir(char *dir)
{
	if (rdir_number < SDIR_MAX) {
		rdir[rdir_number] = dir;
		rdir_number++;
	}
	else {
		fprintf(stderr, "Set too much module search directory.");
		exit(-1);
	}
}

char *
get_default_sdir(void)
{
	static int	need_init = 1;
	static char	dir[512];

	if (need_init) {
		struct utsname	ubuf;

		if (uname(&ubuf)) {
			fprintf(stderr, "Fail to get kernel version.");
			exit(-errno);
		}
		snprintf(dir, 512, "%s/%s/kernel", MOD_DIR, ubuf.release);
	}

	return dir;
}

void
print_usage(char *arg)
{
	printf("Output LKM info in GDB add-symbol-file format.\n"
	       "Usage: %s [option]\n\n"

	       "  -s dir    Add dir to module search directory list.\n"
	       "            This options can use more than once.\n\n"

	       "  -S        Add %s to module search directory list.\n\n"

	       "  -r dir    Add dir to replace the directory.\n"
	       "            This options can use more than once.\n\n"

	       "  -n        No search the directory of the module\n"
	       "            file directory.\n\n"

	       "  -h        Display this information.\n",
	       arg, get_default_sdir());

	exit(0);
}

int
main(int argc,char *argv[],char *envp[])
{
	struct stat	sbuf;
	FILE		*fp;
	char		line[4096];
	int		c;
	int		default_sdir_isset = 0;

	if (geteuid() != 0) {
		fprintf(stderr,
			"Only root can get the right address of modules.\n");
		exit(-1);
	}

	while ((c = getopt(argc, argv, "s:Sr:nh")) != -1) {
		switch (c) {
		case 's':
			add_sdir(optarg);
			break;
		case 'S':
			if (!default_sdir_isset)
				add_sdir(get_default_sdir());
			break;
		case 'r':
			add_rdir(optarg);
			break;
		case 'n':
			no_search_mod = 1;
			break;
		case 'h':
		default:
			print_usage(argv[0]);
			break;
		}
	}

	if (!no_search_mod && sdir_number == 0)
		add_sdir(get_default_sdir());
	if (!no_search_mod && sdir_number == 0) {
		no_search_mod = 1;
		fprintf(stderr, "#Cannot open any module search "
				"directories.  Auto open -n.\n");
	}

	/* Check PROC_MOD.  */
	if (stat(PROC_MOD, &sbuf) || !S_ISREG(sbuf.st_mode)) {
		fprintf(stderr, "%s is not right.\n", PROC_MOD);
		exit(-1);
	}

	/* Get module name and address from PROC_MOD.  */
	fp = fopen(PROC_MOD, "r");
	if (!fp) {
		perror(PROC_MOD);
		exit(-errno);
	}
	while(fgets(line, 4096, fp)) {
		int	i;
		size_t	size = strlen(line);
		int	is_not_digit = 0;

		if (line[size - 1] != '\n') {
			fprintf(stderr, "line:%s is too big to parse by getmod.\n", line);
			exit(-1);
		}

		/* This part get the name.  */
		for (i = 0; i < size; i++) {
			if (line[i] == ' ') {
				line[i] = '\0';
				break;
			}
		}
		/* Following part will get the addr.  */
		if (i == size) {
			fprintf(stderr,
				"The format of \"%s\" is not right.\n", line);
			exit(-1);
		}
		if (line[size - 1] == '\n')
			line[size - 1] = '\0';
		for (i = size - 2; i >= 0; i--) {
			if (line[i] == ' ') {
				if (is_not_digit) {
					line[i] = '\0';
					is_not_digit = 0;
				} else
					break;
			} else {
				if (line[i] != 'x' && line[i] != 'X'
				    && (line[i] < '0' || line[i] > '9')
				    && (line[i] < 'a' || line[i] > 'f')
				    && (line[i] < 'A' || line[i] > 'F'))
					is_not_digit = 1;
			}
		}
		if (i < 0) {
			fprintf(stderr, "The format of \"%s\" is not right.\n",
				line);
			exit(-1);
		}
		print_mod(line, line + i + 1);
	}
	if (ferror(fp)) {
		perror(PROC_MOD);
		exit(-errno);
	}
	fclose(fp);

	return 0;
}
