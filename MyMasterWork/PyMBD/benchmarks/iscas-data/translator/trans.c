/*
 *  Copyright 1987 by the Microelectronics Center of North Carolina.
 *
 *  Author: David S. Bryan
 *  Date: 9/28/88
 *
 *
 * This is a translator from ISCAS '85 netlist format to a more generic
 * netlist format.
 *
 */
#include <stdio.h>
#include <strings.h>

#define  MAX_LINE	256
#define  MAX_WIRES	20000
#define  NAME_LEN	32
#define  TYPE_LEN	5

typedef struct wire
   {
   int  addr;
   char  name[NAME_LEN], type[TYPE_LEN];
   short  fanin, fanout;
   struct fanlist  *flist;
   struct wire  *next;
   } WIRE;

typedef struct fanlist
   {
   WIRE  *wptr;
   struct fanlist  *next;
   } FANLIST;

static WIRE  *head, *stemTable[MAX_WIRES];

/******************************************************************************/

main ()
   {

   read_netlist ();

   write_netlist ();
   }

read_netlist ()
   {
   WIRE  *wptr1, *wptr2;
   FANLIST  *fptr1, *fptr2;
   int   i, ch, inaddr;
   char  *malloc (), line_buf[MAX_LINE];

   head = wptr2 = wptr1 = (WIRE *) malloc (sizeof (WIRE));
   while ((ch = getchar ()) != EOF)
      {
      ungetc (ch,stdin);
      if (ch == '*')
	 {
	 gets (line_buf);
	 printf ("$%s\n",&line_buf[1]);
	 }
      else
	 {
	 scanf ("%d %s %s",&wptr1->addr,wptr1->name,wptr1->type);
	 if (strcmp (wptr1->type,"from") == 0)
	    {
	    scanf ("%*[^\n]%*c");
	    if (MAX_WIRES > wptr1->addr)
	       stemTable[wptr1->addr] = wptr2;
	    else
	       {
	       fputs ("address too large; increase MAX_WIRES\n",stderr);
	       exit (1);
	       }
	    }
	 else
	    {
	    scanf ("%hd %hd%*[^\n]%*c",&wptr1->fanout,&wptr1->fanin);
	    if (MAX_WIRES > wptr1->addr)
	       stemTable[wptr1->addr] = wptr1;
	    else
	       {
	       fputs ("address too large; increase MAX_WIRES\n",stderr);
	       exit (1);
	       }
	    for (i = 0; i < wptr1->fanin; i++)
	       {
	       if ((fptr1 = (FANLIST *) malloc (sizeof (FANLIST))) == NULL)
		  {
		  fputs ("ran out of memory\n",stderr);
		  exit (1);
		  }
	       if (i == 0)
	          wptr1->flist = fptr2 = fptr1;
	       scanf ("%d",&inaddr);
	       if (MAX_WIRES > inaddr)
		  if (stemTable[inaddr] != NULL)
	             fptr1->wptr = stemTable[inaddr];
		  else
		     {
		     fprintf (stderr,"unknown fanin address %d\n",inaddr);
		     exit (1);
		     }
	       else
		  {
		  fputs ("address too large; increase MAX_WIRES\n",stderr);
		  exit (1);
		  }
	       fptr2->next = fptr1;
	       fptr2 = fptr1;
	       fptr1->next = NULL;
	       }
	    if (wptr1->fanin > 0)
	       scanf ("%*[^\n]%*c");
	    else
	       wptr1->flist = NULL;
	    wptr2->next = wptr1;
	    wptr2 = wptr1;
	    wptr1->next = NULL;
	    if ((wptr1 = (WIRE *) malloc (sizeof (WIRE))) == NULL)
	       {
	       fputs ("ran out of memory\n",stderr);
	       exit (1);
	       }
	    }
	 }
      }
   wptr2->next = NULL;
   free ((char *) wptr1);
   }

write_netlist ()
   {
   WIRE  *wptr;
   FANLIST  *fptr;

   wptr = head;
   while (wptr)
      {
      if (wptr->fanin == 0)
	 printf ("%-*s\t$... primary input\n",NAME_LEN,wptr->name);
      wptr = wptr->next;
      }
   puts ("$\n$");
   wptr = head;
   while (wptr)
      {
      if (wptr->fanout == 0)
	 printf ("%-*s\t$... primary output\n",NAME_LEN,wptr->name);
      wptr = wptr->next;
      }
   puts ("$\n$\n$\tOutput\tType\tInputs...");
   puts ("$\t------\t----\t---------");
   wptr = head;
   while (wptr)
      {
      if (strcmp (wptr->type,"inpt") != 0)
	 {
	 printf ("\t%s\t%s",wptr->name,wptr->type);
	 for (fptr = wptr->flist; fptr != NULL; fptr = fptr->next)
	    printf ("\t%s",fptr->wptr->name);
	 puts ("");
	 }
      wptr = wptr->next;
      }
   }

/* end of file */

