/*
 * Put gtprsp comand file to KGTP interface.
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
 * Copyright(C) KGTP team (https://code.google.com/p/kgtp/), 2012
 */

#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>

#define GTP_RW_MAX	16384

#define GTP_FILE	"/sys/kernel/debug/gtp"

int
main(int argc, char *argv[], char *envp[])
{
	FILE	*fd;
	char	buf[GTP_RW_MAX];
	int	gtp;

	if (argc != 2 && argc != 3) {
		printf("Usage: %s gtprsp_file [gtp]\n", argv[0]);
		return -1;
	}

	fd = fopen(argv[1], "r");
	if (fd == NULL) {
		perror(argv[1]);
		exit(-errno);
	}
	if (argc == 2)
		gtp = open(GTP_FILE, O_WRONLY);
	else
		gtp = open(argv[2], O_WRONLY);

	while (fgets(buf, GTP_RW_MAX, fd)) {
		int	i;
		int	buf_size;

		buf_size = strnlen(buf, GTP_RW_MAX);

		/* Try to find $ */
		for (i = 0; i < buf_size; i++) {
			if (buf[i] == '$')
				break;
		}
		if (i >= buf_size) {
			fprintf(stderr, "Drop line \"%s\"\n", buf); 
			continue;
		}

		/* Try to find # */
		for (i = buf_size - 1; i >= 0; i--) {
			if (buf[i] == '#')
				break;
		}
		if (i < 0) {
			fprintf(stderr, "Drop line \"%s\"\n", buf); 
			continue;
		}

		if (write(gtp, buf, strlen(buf)) <= 0)
			fprintf(stderr, "Write line \"%s\" fail\n", buf); 
	}

	fclose(fd);
	close(gtp);

	return 0;
}
